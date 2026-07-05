"""Skill discovery.

Skills are looked up across an ordered list of search paths. Earlier paths
win, so a project-local skill can override a built-in one with the same name.

Default search order:

1. Directories in the ``AGENT_SKILLS_PATH`` environment variable
   (``os.pathsep``-separated).
2. ``./skills`` relative to the current working directory.
3. ``~/.agent-skills/skills`` (the user's personal library).
4. Built-in skills shipped inside this package.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from agent_skills.errors import SkillNotFoundError, SkillParseError
from agent_skills.skill import SKILL_FILENAME, Skill

ENV_VAR = "AGENT_SKILLS_PATH"
_BUILTIN_DIR = Path(__file__).parent / "skills"


def default_search_paths(cwd: Path | None = None) -> list[Path]:
    """Compute the default search path list (highest precedence first)."""
    paths: list[Path] = []
    env_value = os.environ.get(ENV_VAR, "")
    paths.extend(Path(part) for part in env_value.split(os.pathsep) if part)
    paths.append((cwd or Path.cwd()) / "skills")
    paths.append(Path.home() / ".agent-skills" / "skills")
    paths.append(_BUILTIN_DIR)
    return paths


class SkillRegistry:
    """Discovers and loads skills from an ordered list of directories."""

    def __init__(self, search_paths: list[Path] | None = None) -> None:
        self.search_paths = search_paths if search_paths is not None else default_search_paths()

    def discover(self) -> list[Skill]:
        """Return all valid skills, de-duplicated by name (first wins).

        Invalid skill directories are skipped silently during discovery so a
        single broken skill never breaks ``skills list``; loading a broken
        skill *by name* still raises so the author sees the error.
        """
        seen: dict[str, Skill] = {}
        for directory in self._skill_directories():
            try:
                skill = Skill.from_path(directory)
            except SkillParseError:
                continue
            if skill.name not in seen:
                seen[skill.name] = skill
        return sorted(seen.values(), key=lambda skill: skill.name)

    def get(self, name: str) -> Skill:
        """Load a skill by name.

        Raises:
            SkillNotFoundError: If no directory on the search path defines
                the named skill.
            SkillParseError: If the matching SKILL.md is malformed.
        """
        for directory in self._skill_directories():
            if directory.name == name:
                return Skill.from_path(directory)
        # Fall back to declared names (directory name may differ from
        # frontmatter name).
        for skill in self.discover():
            if skill.name == name:
                return skill
        raise SkillNotFoundError(name, available=[skill.name for skill in self.discover()])

    def _skill_directories(self) -> Iterator[Path]:
        for root in self.search_paths:
            if not root.is_dir():
                continue
            for child in sorted(root.iterdir()):
                if child.is_dir() and (child / SKILL_FILENAME).is_file():
                    yield child
