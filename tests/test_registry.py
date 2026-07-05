from __future__ import annotations

from pathlib import Path

import pytest

from agent_skills.errors import SkillNotFoundError
from agent_skills.registry import SkillRegistry, default_search_paths


def _write_skill(root: Path, name: str, description: str = "desc") -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\nInstructions for {name}.",
        encoding="utf-8",
    )
    return directory


class TestDiscover:
    def test_finds_skills_sorted_by_name(self, tmp_path: Path) -> None:
        _write_skill(tmp_path, "zeta")
        _write_skill(tmp_path, "alpha")
        registry = SkillRegistry([tmp_path])
        assert [skill.name for skill in registry.discover()] == ["alpha", "zeta"]

    def test_earlier_path_wins_on_name_conflict(self, tmp_path: Path) -> None:
        first, second = tmp_path / "first", tmp_path / "second"
        _write_skill(first, "dup", description="from first")
        _write_skill(second, "dup", description="from second")
        registry = SkillRegistry([first, second])
        skills = registry.discover()
        assert len(skills) == 1
        assert skills[0].description == "from first"

    def test_broken_skill_is_skipped_in_discovery(self, tmp_path: Path) -> None:
        _write_skill(tmp_path, "good")
        broken = tmp_path / "broken"
        broken.mkdir()
        (broken / "SKILL.md").write_text("no frontmatter here", encoding="utf-8")
        registry = SkillRegistry([tmp_path])
        assert [skill.name for skill in registry.discover()] == ["good"]

    def test_nonexistent_search_path_is_ignored(self, tmp_path: Path) -> None:
        registry = SkillRegistry([tmp_path / "does-not-exist"])
        assert registry.discover() == []


class TestGet:
    def test_get_by_name(self, tmp_path: Path) -> None:
        _write_skill(tmp_path, "target")
        assert SkillRegistry([tmp_path]).get("target").name == "target"

    def test_get_missing_raises_with_suggestions(self, tmp_path: Path) -> None:
        _write_skill(tmp_path, "existing")
        with pytest.raises(SkillNotFoundError, match="Available skills: existing"):
            SkillRegistry([tmp_path]).get("nope")


class TestDefaultSearchPaths:
    def test_env_var_paths_come_first(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        custom = tmp_path / "custom"
        monkeypatch.setenv("AGENT_SKILLS_PATH", str(custom))
        paths = default_search_paths(cwd=tmp_path)
        assert paths[0] == custom
        assert paths[1] == tmp_path / "skills"

    def test_builtins_are_last_and_exist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AGENT_SKILLS_PATH", raising=False)
        builtin = default_search_paths()[-1]
        assert builtin.is_dir()
        assert any(child.is_dir() for child in builtin.iterdir())

    def test_builtin_skills_all_parse(self) -> None:
        registry = SkillRegistry([default_search_paths()[-1]])
        names = {skill.name for skill in registry.discover()}
        assert names == {
            "dockerfile-review",
            "k8s-crashloop",
            "postgres-diagnose",
            "stacktrace-explain",
        }
