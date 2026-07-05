"""Compose a skill and user input into a prompt, then execute it."""

from __future__ import annotations

from dataclasses import dataclass

from agent_skills.providers import Provider
from agent_skills.skill import Skill

_PROMPT_TEMPLATE = """\
<input>
{input_text}
</input>

{task}"""

_DEFAULT_TASK = "Apply your instructions to the input above."


@dataclass(frozen=True, slots=True)
class RunResult:
    """The outcome of executing a skill."""

    skill_name: str
    output: str


class Runner:
    """Executes skills against input text using an injected provider."""

    def __init__(self, provider: Provider) -> None:
        self._provider = provider

    def run(self, skill: Skill, input_text: str, *, task: str | None = None) -> RunResult:
        """Execute ``skill`` against ``input_text``.

        Args:
            skill: The skill to execute.
            input_text: The material to analyze (log, query, file contents...).
            task: Optional extra instruction from the user, e.g.
                ``"focus on index usage"``.
        """
        prompt = build_prompt(input_text, task=task)
        output = self._provider.complete(system=skill.instructions, prompt=prompt)
        return RunResult(skill_name=skill.name, output=output)


def build_prompt(input_text: str, *, task: str | None = None) -> str:
    """Build the user-turn prompt sent to the provider."""
    return _PROMPT_TEMPLATE.format(
        input_text=input_text.strip(),
        task=(task or _DEFAULT_TASK).strip(),
    )
