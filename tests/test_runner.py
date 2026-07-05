from __future__ import annotations

from agent_skills.runner import Runner, build_prompt
from agent_skills.skill import Skill

from .conftest import VALID_SKILL, FakeProvider


class TestBuildPrompt:
    def test_wraps_input_in_tags(self) -> None:
        prompt = build_prompt("SELECT 1;")
        assert "<input>\nSELECT 1;\n</input>" in prompt
        assert "Apply your instructions" in prompt

    def test_custom_task_replaces_default(self) -> None:
        prompt = build_prompt("data", task="focus on index usage")
        assert prompt.endswith("focus on index usage")
        assert "Apply your instructions" not in prompt


class TestRunner:
    def test_sends_skill_instructions_as_system_prompt(self, fake_provider: FakeProvider) -> None:
        skill = Skill.from_text(VALID_SKILL)
        result = Runner(fake_provider).run(skill, "some input")

        assert result.skill_name == "demo-skill"
        assert result.output == "fake-output"
        assert len(fake_provider.calls) == 1
        call = fake_provider.calls[0]
        assert call["system"] == skill.instructions
        assert "some input" in call["prompt"]
