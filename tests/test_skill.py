from __future__ import annotations

from pathlib import Path

import pytest

from agent_skills.errors import SkillParseError
from agent_skills.skill import Skill

from .conftest import VALID_SKILL


class TestFromText:
    def test_parses_valid_skill(self) -> None:
        skill = Skill.from_text(VALID_SKILL)
        assert skill.name == "demo-skill"
        assert skill.description == "A demo skill for testing."
        assert skill.tags == ("testing", "demo")
        assert skill.version == "1.2.3"
        assert skill.instructions == "You are a demo assistant. Echo wisdom."

    def test_single_string_tag_is_normalized(self) -> None:
        text = "---\nname: x\ndescription: y\ntags: solo\n---\nbody"
        assert Skill.from_text(text).tags == ("solo",)

    def test_missing_frontmatter_raises(self) -> None:
        with pytest.raises(SkillParseError, match="Missing YAML frontmatter"):
            Skill.from_text("just a plain file")

    def test_unterminated_frontmatter_raises(self) -> None:
        with pytest.raises(SkillParseError, match="Unterminated frontmatter"):
            Skill.from_text("---\nname: x\ndescription: y\nno closing delimiter")

    def test_missing_name_raises(self) -> None:
        with pytest.raises(SkillParseError, match="missing required field 'name'"):
            Skill.from_text("---\ndescription: y\n---\nbody")

    def test_missing_description_raises(self) -> None:
        with pytest.raises(SkillParseError, match="missing required field 'description'"):
            Skill.from_text("---\nname: x\n---\nbody")

    def test_empty_body_raises(self) -> None:
        with pytest.raises(SkillParseError, match="empty instructions"):
            Skill.from_text("---\nname: x\ndescription: y\n---\n   \n")

    def test_invalid_yaml_raises(self) -> None:
        with pytest.raises(SkillParseError, match="Invalid YAML"):
            Skill.from_text("---\nname: [unclosed\n---\nbody")

    def test_non_mapping_frontmatter_raises(self) -> None:
        with pytest.raises(SkillParseError, match="must be a YAML mapping"):
            Skill.from_text("---\n- a\n- b\n---\nbody")


class TestFromPath:
    def test_loads_from_directory(self, skills_dir: Path) -> None:
        skill = Skill.from_path(skills_dir / "demo-skill")
        assert skill.name == "demo-skill"
        assert skill.path == skills_dir / "demo-skill" / "SKILL.md"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SkillParseError, match=r"No SKILL\.md"):
            Skill.from_path(tmp_path)
