# agent-skills-cli

**Package expert knowledge as reusable AI agent skills — and run them from your terminal.**

[![CI](https://github.com/ridhima01/agent-skills-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/ridhima01/agent-skills-cli/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A *skill* is a directory with a `SKILL.md` file: YAML frontmatter plus markdown
instructions that turn a general-purpose LLM into a focused specialist — a
PostgreSQL triage engineer, a Kubernetes SRE, a Dockerfile security reviewer.
Write the expertise once, version it in git, share it with your team, and run
it against any log, query, or file:

```console
$ skills run postgres-diagnose --file slow_query.sql
$ cat pod.log | skills run k8s-crashloop
$ skills run dockerfile-review --file Dockerfile --task "focus on image size"
```

I built the first version of this idea at work to help my team troubleshoot
production PostgreSQL issues with AI assistance. This is the generalized,
open-source rewrite: a tiny framework for *any* operational skill.

## Why

Everyone on your team prompts the LLM differently, so answer quality is a
lottery. The debugging checklist that lives in a senior engineer's head — what
to look at first, what the usual suspects are, what output format is useful —
is exactly what belongs in a versioned, reviewable artifact. Skills make
prompts what they should have been all along: **code**.

- **Skills are just files.** Review them in PRs, diff them, ship them with your repo.
- **Project-local overrides.** A `./skills/` directory in your repo beats the built-ins, so each project can carry its own tuned expertise.
- **Composable input.** Files, stdin pipes, or inline text — it fits into the shell workflows you already have.

## Install

```console
pip install agent-skills-cli
export ANTHROPIC_API_KEY=sk-ant-...   # https://console.anthropic.com/
```

## Quickstart

```console
$ skills list
dockerfile-review   Review a Dockerfile for security issues, image size, and build-cache efficiency.  [docker, security, devops]
k8s-crashloop       Triage CrashLoopBackOff, OOMKilled, and failing pods from kubectl output.  [kubernetes, sre, infra]
postgres-diagnose   Diagnose slow queries, locks, bloat, and connection issues in PostgreSQL.  [database, postgres, performance]
stacktrace-explain  Explain any stack trace, find the root cause frame, and suggest a fix.  [debugging, errors]

$ kubectl describe pod api-7d4b9 | skills run k8s-crashloop
Failure class: OOMKilled (exit code 137)
Evidence: ...
Fix:
  resources:
    limits:
      memory: "512Mi"   # was 256Mi
...
```

Inspect what a skill will actually do before running it:

```console
$ skills show postgres-diagnose
```

## Write your own skill in 2 minutes

Create `./skills/changelog-writer/SKILL.md` in any project:

```markdown
---
name: changelog-writer
description: Turn a git log into a clean, user-facing changelog.
tags: [git, release]
---

You are a release manager. The input is `git log` output.
Group changes into Added / Changed / Fixed / Removed...
```

That's it — no registration step:

```console
$ git log v1.2.0..HEAD --oneline | skills run changelog-writer
```

**Skill discovery order** (first match wins, so you can override built-ins):

1. `$AGENT_SKILLS_PATH` (colon-separated directories)
2. `./skills/` in the current directory
3. `~/.agent-skills/skills/` — your personal library
4. Built-in skills shipped with the package

## Architecture

```
CLI (argparse) ──▶ SkillRegistry ──▶ Runner ──▶ Provider (Protocol)
                   finds SKILL.md     builds       └── AnthropicProvider
                   on search paths    the prompt   └── FakeProvider (tests)
```

Design choices, briefly:

- **`Provider` is a `Protocol`**, not a base class. The whole test suite runs
  against a fake with zero network calls, and adding another vendor is one
  new class — nothing else changes.
- **Frozen dataclasses** for `Skill` and `RunResult`: parse once, then
  immutable and hashable everywhere downstream.
- **Discovery never crashes on a broken skill** (a bad `SKILL.md` shouldn't
  take down `skills list`), but loading a broken skill *by name* raises with
  a precise parse error so authors get fast feedback.
- **Errors are a small hierarchy** rooted at `SkillError`, so the CLI boundary
  is a single `except` that turns any domain failure into a clean exit code 1.

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | API key (required) | — |
| `ANTHROPIC_MODEL` | Override the model | `claude-sonnet-4-6` |
| `AGENT_SKILLS_PATH` | Extra skill directories | — |

Per-invocation: `skills run <name> --model <model>`.

## Development

```console
git clone https://github.com/ridhima01/agent-skills-cli
cd agent-skills-cli
pip install -e ".[dev]"
pytest          # tests + coverage
ruff check .    # lint
mypy            # strict type checking
```

## Roadmap

- [ ] Streaming output (`--stream`)
- [ ] OpenAI-compatible provider
- [ ] `skills init <name>` scaffolding command
- [ ] Multi-file input (`--file a.log --file b.log`)

## License

MIT © Ridhima Goyal
