from __future__ import annotations

import sys
from dataclasses import dataclass
from io import StringIO

import pytest

from agent_skills import cli
from agent_skills.errors import ProviderError
from agent_skills.providers import DEFAULT_MODEL, AnthropicProvider, Provider

from .conftest import FakeProvider


class TestAnthropicProvider:
    def test_missing_api_key_raises_helpful_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ProviderError, match="ANTHROPIC_API_KEY is not set"):
            AnthropicProvider()

    def test_model_resolution_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
        assert AnthropicProvider()._model == DEFAULT_MODEL

        monkeypatch.setenv("ANTHROPIC_MODEL", "env-model")
        assert AnthropicProvider()._model == "env-model"
        assert AnthropicProvider(model="arg-model")._model == "arg-model"

    def test_api_failure_wrapped_in_provider_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider()

        class Boom:
            def create(self, **_: object) -> object:
                raise RuntimeError("connection refused")

        monkeypatch.setattr(provider._client, "messages", Boom())
        with pytest.raises(ProviderError, match="connection refused"):
            provider.complete(system="s", prompt="p")

    def test_empty_completion_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        provider = AnthropicProvider()

        @dataclass
        class FakeResponse:
            content: list[object]

        class Empty:
            def create(self, **_: object) -> FakeResponse:
                return FakeResponse(content=[])

        monkeypatch.setattr(provider._client, "messages", Empty())
        with pytest.raises(ProviderError, match="empty completion"):
            provider.complete(system="s", prompt="p")

    def test_satisfies_provider_protocol(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert isinstance(AnthropicProvider(), Provider)
        assert isinstance(FakeProvider(), Provider)


class TestStdinInput:
    @pytest.fixture(autouse=True)
    def isolated_registry(self, skills_dir: object, monkeypatch: pytest.MonkeyPatch) -> None:
        from pathlib import Path

        from agent_skills.registry import SkillRegistry

        assert isinstance(skills_dir, Path)
        monkeypatch.setattr(cli, "SkillRegistry", lambda: SkillRegistry([skills_dir]))

    def test_run_reads_piped_stdin(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        provider = FakeProvider(response="from-stdin")
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: provider)

        fake_stdin = StringIO("piped log line\n")
        fake_stdin.isatty = lambda: False  # type: ignore[method-assign]
        monkeypatch.setattr(sys, "stdin", fake_stdin)

        assert cli.main(["run", "demo-skill"]) == 0
        assert "from-stdin" in capsys.readouterr().out
        assert "piped log line" in provider.calls[0]["prompt"]

    def test_no_input_on_tty_errors(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(cli, "AnthropicProvider", lambda model=None: FakeProvider())

        fake_stdin = StringIO()
        fake_stdin.isatty = lambda: True  # type: ignore[method-assign]
        monkeypatch.setattr(sys, "stdin", fake_stdin)

        assert cli.main(["run", "demo-skill"]) == 1
        assert "No input provided" in capsys.readouterr().err
