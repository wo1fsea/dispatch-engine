---
name: dispatch-engine
description: Runtime-backed Codex skill for supervising repo-native agent work. Use when a user wants to inspect a repository's own planning conventions, turn an objective into schedulable workstreams, run or resume a local Dispatch Engine loop, monitor agent workers/reviewers, resolve pending decisions, or package the bundled runtime for direct skill installation.
---

# Dispatch Engine

Use this skill to operate the bundled Dispatch Engine runtime from a repository or task context.

Dispatch Engine is a skill-first project: the skill root contains the operator instructions, the runnable local CLI, runtime modules, and reference protocols. A user should be able to clone or copy this directory into their Codex skills directory and have the runtime available through the bundled scripts.

## Core Rule

Treat the bundled runtime as the execution source of truth. Do not reimplement scheduling, event logging, status parsing, or worker prompt generation by hand when a `scripts/de.py` command can do it.

## Runtime Location

Resolve paths relative to this `SKILL.md` file:

```text
scripts/de.py                 # CLI entrypoint
scripts/dispatch_engine/      # bundled runtime package
references/                   # operator and protocol guidance
```

Use:

```bash
python scripts/de.py --help
python scripts/de.py inspect <repo>
python scripts/de.py plan <repo> --objective "<objective>"
python scripts/de.py status <repo>
```

## Operating Flow

1. Read the target repository's local instructions before dispatching work.
2. Run `python scripts/de.py inspect <repo>` to discover instructions, planning sources, scripts, and validation hints.
3. Run `python scripts/de.py plan <repo> --objective "<objective>"` before starting work when the objective is ambiguous, cross-module, or likely to need multiple agents.
4. Ask the user before running worker agents when the plan contains pending decisions, high-risk surfaces, or parallel workstreams.
5. Run or resume the Dispatch Engine loop through the bundled CLI.
6. Monitor status through CLI output and run-state files, not through chat memory alone.
7. Resolve pending decisions explicitly before continuing blocked work.
8. Record validation evidence before claiming a run is complete.

## Packaging Rule

Before telling a user to install or copy this skill, verify that the runnable runtime is present under `scripts/` and that the basic CLI smoke checks pass:

```bash
python scripts/de.py --help
python scripts/de.py version
```

If runtime code has moved or been rebuilt elsewhere, copy or vendor the current runtime back into this skill directory before installation guidance.

## Reference Files

- Read `references/operator-flow.md` when supervising a run from interactive Codex.
- Read `references/event-protocol.md` when changing run-state or event-log behavior.
- Read `references/worker-protocol.md` when changing worker or reviewer adapters.
