"""Command-line interface.

Usage::

    skills list
    skills show postgres-diagnose
    skills run postgres-diagnose --file slow_query.sql
    cat pod.log | skills run k8s-crashloop
    skills run stacktrace-explain --text "Traceback (most recent call last): ..."
"""

from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path

from agent_skills import __version__
from agent_skills.errors import SkillError
from agent_skills.providers import DEFAULT_MODEL, AnthropicProvider
from agent_skills.registry import SkillRegistry
from agent_skills.runner import Runner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills",
        description="Run reusable AI agent skills against files, stdin, or inline text.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all discoverable skills")

    show = subparsers.add_parser("show", help="Show a skill's metadata and instructions")
    show.add_argument("name", help="Skill name")

    run = subparsers.add_parser("run", help="Run a skill against input")
    run.add_argument("name", help="Skill name")
    source = run.add_mutually_exclusive_group()
    source.add_argument("--file", type=Path, help="Read input from a file")
    source.add_argument("--text", help="Pass input inline")
    run.add_argument("--task", help="Extra instruction, e.g. 'focus on index usage'")
    run.add_argument("--model", help=f"Override the model (default: {DEFAULT_MODEL})")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = SkillRegistry()
    try:
        if args.command == "list":
            return _cmd_list(registry)
        if args.command == "show":
            return _cmd_show(registry, args.name)
        return _cmd_run(registry, args)
    except SkillError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        # Output was piped to a consumer that closed early (e.g. `| head`).
        _silence_stdout()
        return 141


def _silence_stdout() -> None:
    """Point stdout at devnull so Python's shutdown flush doesn't raise after SIGPIPE."""
    with contextlib.suppress(OSError, ValueError):
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())


def _cmd_list(registry: SkillRegistry) -> int:
    skills = registry.discover()
    if not skills:
        print("No skills found. Add one under ./skills/<name>/SKILL.md")
        return 0
    width = max(len(skill.name) for skill in skills)
    for skill in skills:
        tags = f"  [{', '.join(skill.tags)}]" if skill.tags else ""
        print(f"{skill.name:<{width}}  {skill.description}{tags}")
    return 0


def _cmd_show(registry: SkillRegistry, name: str) -> int:
    skill = registry.get(name)
    print(f"name:        {skill.name}")
    print(f"description: {skill.description}")
    print(f"version:     {skill.version}")
    if skill.tags:
        print(f"tags:        {', '.join(skill.tags)}")
    if skill.path:
        print(f"path:        {skill.path}")
    print("\n--- instructions ---\n")
    print(skill.instructions)
    return 0


def _read_input(args: argparse.Namespace) -> str:
    file: Path | None = args.file
    text: str | None = args.text
    if file is not None:
        if not file.is_file():
            raise SkillError(f"Input file not found: {file}")
        return file.read_text(encoding="utf-8")
    if text is not None:
        return text
    if sys.stdin.isatty():
        raise SkillError("No input provided. Use --file, --text, or pipe via stdin.")
    return sys.stdin.read()


def _cmd_run(registry: SkillRegistry, args: argparse.Namespace) -> int:
    skill = registry.get(args.name)
    input_text = _read_input(args)
    if not input_text.strip():
        raise SkillError("Input is empty.")
    provider = AnthropicProvider(model=args.model)
    result = Runner(provider).run(skill, input_text, task=args.task)
    print(result.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
