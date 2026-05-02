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
python scripts/de.py run <repo> --dry-run
python scripts/de.py run <repo> --provider codex --dry-run
python scripts/de.py run <repo> --provider claude --dry-run
python scripts/de.py status <repo>
python scripts/de.py tail <repo>
```

`de run <repo> --dry-run` renders a provider CLI coordinator launch without
starting a provider process. When `--provider` is omitted, the runtime uses
provider `codex` and renders a Codex CLI command shape based on `codex exec`.
`--provider codex` renders the same provider/profile explicitly.
`--provider claude` renders a Claude CLI command shape based on `claude -p`.
Dry-run output includes the resolved command, run id, state directory, and
coordinator prompt marker or preview; it does not launch Codex, Claude, or any
other provider process.

Runtime prompt templates are centralized under `references/prompts/`. Do not
embed provider, coordinator, worker, reviewer, or validator prompt text directly
in runtime modules.

## Operating Flow

1. Read the target repository's local instructions before dispatching work.
2. Use interactive Codex judgment to summarize the repository rules, planning basis, validation strategy, workstreams, dependencies, write scopes, and pending decisions.
3. Write any Dispatch Engine-generated plan file under `.dispatch/plans/` in the target repository.
4. Import the explicit plan into runtime state with `python scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json`.
5. Render the coordinator launch with `python scripts/de.py run <repo> --dry-run`; omit `--provider` for the default Codex coordinator, or pass `--provider codex` or `--provider claude` explicitly.
6. Ask the user before worker execution when the plan contains pending decisions, high-risk surfaces, or parallel workstreams.
7. Run or resume the future Dispatch Engine orchestrator loop from imported plan state.
8. Monitor status through CLI output and `.dispatch/runs/` files, not through chat memory alone.
9. Resolve pending decisions explicitly before continuing blocked work.
10. Record validation evidence before claiming a run is complete.

## Coordinator And Agent Protocol

Provider CLI processes are coordinators only. A coordinator may plan, dispatch,
monitor, review, summarize, request decisions, and write Dispatch Engine runtime
state under `.dispatch/`; it must not directly implement project-file changes.
Project implementation belongs to registered workers, reviewers, or validators.

Workers, reviewers, and validators must be registered before their output is
treated as valid. Registry records live under:

```text
.dispatch/runs/<run-id>/agents/
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/logs/
.dispatch/runs/<run-id>/heartbeats/
```

`de status` reads these files to report coordinator provider/profile/status,
agent counts by role and status, active assignments, heartbeat counts, pending
decisions, and protocol violations. Lifecycle events include
`coordinator.started`, `agent.spawned`, `agent.heartbeat`,
`workstream.assigned`, `agent.completed`, `agent.failed`,
`protocol.violation`, and `decision.requested`.

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
- Read `references/prompts/` when changing runtime prompt templates.
