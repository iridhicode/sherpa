"""Exception hierarchy for agent-skills-cli.

All exceptions derive from :class:`SkillError` so callers can catch a single
base class at the CLI boundary while library users can handle specific cases.
"""

from __future__ import annotations


class SkillError(Exception):
    """Base class for all agent-skills errors."""


class SkillParseError(SkillError):
    """A SKILL.md file exists but could not be parsed."""


class SkillNotFoundError(SkillError):
    """No skill with the requested name exists on the search path."""

    def __init__(self, name: str, available: list[str] | None = None) -> None:
        self.name = name
        self.available = available or []
        hint = f" Available skills: {', '.join(self.available)}." if self.available else ""
        super().__init__(f"Skill '{name}' not found.{hint}")


class ProviderError(SkillError):
    """The LLM provider failed to produce a completion."""
