"""agent-skills-cli: package expert knowledge as reusable AI agent skills.

A *skill* is a directory containing a ``SKILL.md`` file: YAML frontmatter
(name, description, tags) followed by markdown instructions that become the
system prompt for an LLM. Skills are discovered from configurable search
paths and executed against arbitrary input (files, stdin, or inline text).
"""

from agent_skills.errors import ProviderError, SkillError, SkillNotFoundError, SkillParseError
from agent_skills.registry import SkillRegistry
from agent_skills.runner import Runner
from agent_skills.skill import Skill

__version__ = "0.1.0"

__all__ = [
    "ProviderError",
    "Runner",
    "Skill",
    "SkillError",
    "SkillNotFoundError",
    "SkillParseError",
    "SkillRegistry",
    "__version__",
]
