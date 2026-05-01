---
name: dispatch-engine
description: Runtime-backed Codex skill for supervising repo-native agent work. Use when a user wants interactive Codex to read a repository's own planning conventions, prepare an explicit dispatch plan, import that plan into durable Dispatch Engine state, monitor agent workers/reviewers, resolve pending decisions, or package the bundled runtime for direct skill installation.
---

# Dispatch Engine

Use this skill to operate the bundled Dispatch Engine runtime from a repository or task context.

Dispatch Engine is a skill-first project: the skill root contains the operator instructions, the runnable local CLI, runtime modules, and reference protocols. A user should be able to clone or copy this directory into their Codex skills directory and have the runtime available through the bundled scripts.

## Boundary Rule

Interactive Codex plus this skill owns repository discovery, planning judgment, workstream splitting, review, and user conversation. The bundled runtime owns explicit plan import, durable `.dispatch/` run state, event logging, status/tail readers, and the future mechanical orchestrator loop.

Dispatch Engine-generated non-project runtime content in a target repository belongs only under `.dispatch/`. Project files changed to satisfy the user's objective remain in the target repository's normal project paths.

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
python scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json
python scripts/de.py status <repo>
python scripts/de.py tail <repo>
```

## Operating Flow

1. Read the target repository's local instructions before dispatching work.
2. Use interactive Codex judgment to summarize the repository rules, planning basis, validation strategy, workstreams, dependencies, write scopes, and pending decisions.
3. Write any Dispatch Engine-generated plan file under `.dispatch/plans/` in the target repository.
4. Import the explicit plan into runtime state with `python scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json`.
5. Ask the user before worker execution when the plan contains pending decisions, high-risk surfaces, or parallel workstreams.
6. Run or resume the future Dispatch Engine orchestrator loop from imported plan state.
7. Monitor status through CLI output and `.dispatch/runs/` files, not through chat memory alone.
8. Resolve pending decisions explicitly before continuing blocked work.
9. Record validation evidence before claiming a run is complete.

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
- Read `references/orchestrator-loop.md` when designing the future runtime scheduler, worker, reviewer, validation, and status/tail loop.
