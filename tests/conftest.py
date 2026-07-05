"""Shared fixtures. No test in this suite touches the network."""

from __future__ import annotations

from pathlib import Path

import pytest

VALID_SKILL = """\
---
name: demo-skill
description: A demo skill for testing.
tags: [testing, demo]
version: 1.2.3
---

You are a demo assistant. Echo wisdom.
"""


class FakeProvider:
    """Records calls and returns a canned response."""

    def __init__(self, response: str = "fake-output") -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def complete(self, *, system: str, prompt: str) -> str:
        self.calls.append({"system": system, "prompt": prompt})
        return self.response


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    """A temp directory containing one valid skill: demo-skill."""
    skill_dir = tmp_path / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    return tmp_path / "skills"
