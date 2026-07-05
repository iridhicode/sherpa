from __future__ import annotations

from pathlib import Path

import pytest

from agent_skills import cli
from agent_skills.registry import SkillRegistry

from .conftest import FakeProvider


@pytest.fixture(autouse=True)
def isolated_registry(skills_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the CLI at the temp skills dir only, for deterministic tests."""
    monkeypatch.setattr(cli, "SkillRegistry", lambda: SkillRegistry([skills_dir]))


class TestList:
    def test_lists_skills(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli.main(["list"]) == 0
        out = capsys.readouterr().out
        assert "demo-skill" in out
        assert "A demo skill for testing." in out

    def test_empty_registry_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(cli, "SkillRegistry", lambda: SkillRegistry([tmp_path / "none"]))
        assert cli.main(["list"]) == 0
        assert "No skills found" in capsys.readouterr().out


class TestShow:
    def test_shows_metadata_and_instructions(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli.main(["show", "demo-skill"]) == 0
        out = capsys.readouterr().out
        assert "name:        demo-skill" in out
        assert "Echo wisdom." in out

    def test_unknown_skill_errors(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli.main(["show", "missing"]) == 1
        assert "not found" in capsys.readouterr().err


class TestRun:
    def test_run_with_text_input(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        provider = FakeProvider(response="diagnosis here")
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: provider)

        assert cli.main(["run", "demo-skill", "--text", "SELECT 1;"]) == 0
        assert "diagnosis here" in capsys.readouterr().out
        assert "SELECT 1;" in provider.calls[0]["prompt"]

    def test_run_with_file_input(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        provider = FakeProvider()
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: provider)
        input_file = tmp_path / "query.sql"
        input_file.write_text("SELECT * FROM users;", encoding="utf-8")

        assert cli.main(["run", "demo-skill", "--file", str(input_file)]) == 0
        assert "SELECT * FROM users;" in provider.calls[0]["prompt"]

    def test_run_with_task_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        provider = FakeProvider()
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: provider)

        assert cli.main(["run", "demo-skill", "--text", "x", "--task", "be brief"]) == 0
        assert provider.calls[0]["prompt"].endswith("be brief")

    def test_missing_input_file_errors(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: FakeProvider())
        assert cli.main(["run", "demo-skill", "--file", "/nope/missing.txt"]) == 1
        assert "Input file not found" in capsys.readouterr().err

    def test_empty_input_errors(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: FakeProvider())
        assert cli.main(["run", "demo-skill", "--text", "   "]) == 1
        assert "Input is empty" in capsys.readouterr().err


class TestBrokenPipe:
    def test_broken_pipe_exits_with_sigpipe_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def explode(*_: object) -> int:
            raise BrokenPipeError

        monkeypatch.setattr(cli, "_cmd_list", explode)
        monkeypatch.setattr(cli, "_silence_stdout", lambda: None)
        assert cli.main(["list"]) == 141
