"""The :class:`Skill` model and the ``SKILL.md`` parser.

A skill file looks like::

    ---
    name: postgres-diagnose
    description: Diagnose slow or failing PostgreSQL queries.
    tags: [database, postgres]
    ---

    You are a senior PostgreSQL engineer...

The frontmatter is YAML; everything after the second ``---`` becomes the
system prompt (``instructions``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from agent_skills.errors import SkillParseError

SKILL_FILENAME = "SKILL.md"
_DELIMITER = "---"


@dataclass(frozen=True, slots=True)
class Skill:
    """An immutable, validated skill definition."""

    name: str
    description: str
    instructions: str
    tags: tuple[str, ...] = field(default=())
    version: str = "0.1.0"
    path: Path | None = None

    @classmethod
    def from_text(cls, text: str, *, path: Path | None = None) -> Skill:
        """Parse a ``SKILL.md`` document from a string.

        Raises:
            SkillParseError: If frontmatter is missing, malformed, or
                required fields are absent/empty.
        """
        frontmatter, instructions = _split_frontmatter(text, path=path)
        try:
            meta = yaml.safe_load(frontmatter)
        except yaml.YAMLError as exc:
            raise SkillParseError(
                f"Invalid YAML frontmatter in {path or '<string>'}: {exc}"
            ) from exc

        if not isinstance(meta, dict):
            raise SkillParseError(f"Frontmatter must be a YAML mapping in {path or '<string>'}")

        name = str(meta.get("name", "")).strip()
        description = str(meta.get("description", "")).strip()
        if not name:
            raise SkillParseError(f"Skill is missing required field 'name' ({path or '<string>'})")
        if not description:
            raise SkillParseError(f"Skill '{name}' is missing required field 'description'")
        if not instructions.strip():
            raise SkillParseError(f"Skill '{name}' has empty instructions body")

        raw_tags = meta.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        tags = tuple(str(tag).strip() for tag in raw_tags if str(tag).strip())

        return cls(
            name=name,
            description=description,
            instructions=instructions.strip(),
            tags=tags,
            version=str(meta.get("version", "0.1.0")),
            path=path,
        )

    @classmethod
    def from_path(cls, directory: Path) -> Skill:
        """Load a skill from a directory containing ``SKILL.md``."""
        skill_file = directory / SKILL_FILENAME
        if not skill_file.is_file():
            raise SkillParseError(f"No {SKILL_FILENAME} found in {directory}")
        return cls.from_text(skill_file.read_text(encoding="utf-8"), path=skill_file)


def _split_frontmatter(text: str, *, path: Path | None) -> tuple[str, str]:
    """Split a document into (frontmatter, body).

    The document must start with ``---`` and contain a closing ``---`` line.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _DELIMITER:
        raise SkillParseError(f"Missing YAML frontmatter in {path or '<string>'}")

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _DELIMITER:
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            return frontmatter, body

    raise SkillParseError(f"Unterminated frontmatter in {path or '<string>'}")
