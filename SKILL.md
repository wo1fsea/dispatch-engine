---
name: dispatch-engine
description: Runtime-backed Codex skill for supervising repo-native agent work. Use when a user wants interactive Codex to read a repository's own planning conventions, prepare an explicit dispatch plan, import that plan into durable Dispatch Engine state, monitor agent workers/reviewers, resolve pending decisions, or package the bundled runtime for direct skill installation.
---

# Dispatch Engine

Use this skill to operate the bundled Dispatch Engine runtime from a repository or task context.

Dispatch Engine is a skill-first project: the skill root contains the operator instructions, the runnable local CLI, runtime modules, and reference protocols. A user should be able to clone or copy this directory into their Codex skills directory and have the runtime available through the bundled scripts.

The bundled `de` CLI is a Codex-facing machine interface, not the human user
interface. Humans talk to interactive Codex; interactive Codex calls `de`,
reads JSON/file state, and explains progress or decisions in conversation.

For install, target repo quickstart, progress watching, git ignore guidance,
and troubleshooting, read `references/operator-guide.md`. For detached-run
heartbeat guidance, read `references/heartbeat-observation.md`.

## Boundary Rule

Interactive Codex plus this skill owns repository discovery, planning judgment, workstream splitting, review, and user conversation. The bundled runtime owns explicit plan import, durable `.dispatch/` run state, foreground provider CLI coordinator launch, event logging, status/tail readers, and future mechanical helpers only where durable/queryable state is required.

Dispatch Engine-generated non-project runtime content in a target repository belongs only under `.dispatch/`. Project files changed to satisfy the user's objective remain in the target repository's normal project paths.

## Skill-First Principle

Prefer skill/reference/prompt guidance over runtime code. Workflow judgment,
role behavior, provider-native spawn guidance, review criteria, validation
expectations, blocked-decision handling, and operator runbooks should live in
this skill and `references/` unless runtime code is truly needed.

Add behavior to `scripts/dispatch_engine/` only when it must be durable,
queryable, resumable, mechanically validated, or surfaced through `de status`
or `de tail`. This keeps Dispatch Engine a small runtime-backed skill instead
of a provider-specific agent platform.

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
python scripts/de.py run <repo>
python scripts/de.py run <repo> --detach
python scripts/de.py run <repo> --dry-run
python scripts/de.py run <repo> --provider codex --dry-run
python scripts/de.py run <repo> --provider claude --dry-run
python scripts/de.py status <repo>
python scripts/de.py events <repo> --since event-000001 --json
python scripts/de.py alerts <repo> --json
python scripts/de.py resolve-decision <repo> --id <decision-id> --option <option-id> --json
python scripts/de.py tail <repo>
```

`de run <repo>` launches the latest imported run's provider CLI coordinator in
the foreground. `de run <repo> --detach` starts a background supervisor and
returns immediately so interactive Codex can keep talking with the user while
`de status` and `de tail` expose progress. When `--provider` is omitted, the
runtime uses provider `codex` and launches a Codex CLI command shape based on
`codex exec`. `--provider codex` selects the same provider/profile explicitly.
`--provider claude` launches a Claude CLI command shape based on `claude -p`.

`de run <repo> --dry-run` renders the provider command and coordinator prompt
without starting Codex, Claude, or any other provider process, and without
writing run state. Dry-run output includes the resolved command, run id, state
directory, and coordinator prompt marker or preview.

Detached execution does not make the foreground chat automatically aware of
background changes. For every interactive `de run --detach` launch, interactive
Codex must create a host-provided thread heartbeat/wakeup immediately after the
detached launch succeeds, then use that heartbeat to check Dispatch Engine
state until the run reaches a terminal state. When the run completes, fails, or
is cancelled, interactive Codex must pause, delete, or otherwise stop the
heartbeat. Dispatch Engine itself does not send chat messages or wake the
thread; heartbeat lifecycle belongs to the Codex host layer.

Live runs write a prompt snapshot and process logs under the target repository's
run state:

```text
.dispatch/runs/<run-id>/prompts/coordinator-001.md
.dispatch/runs/<run-id>/logs/coordinator-001.stdout.log
.dispatch/runs/<run-id>/logs/coordinator-001.stderr.log
```

Detached launches also write:

```text
.dispatch/runs/<run-id>/supervisors/coordinator-001.json
.dispatch/runs/<run-id>/logs/coordinator-001.supervisor.stdout.log
.dispatch/runs/<run-id>/logs/coordinator-001.supervisor.stderr.log
```

Codex and Claude receive a short instruction that points to the recorded prompt
snapshot path. Do not embed the full rendered coordinator prompt directly in
provider launch argv.

Runtime prompt templates are centralized under `references/prompts/`. Do not
embed provider, coordinator, worker, reviewer, or validator prompt text directly
in runtime modules. Coordinator prompts are rendered from
`references/prompts/coordinator-protocol.md`, written as run-scoped snapshots,
and passed to provider CLIs through a short prompt-file instruction.
Worker prompts are rendered from `references/prompts/worker-protocol.md` and
must carry the repo, run id, state directory, assigned workstream, assigned
files, allowed write roots, validation expectations, and report path.

## Operating Flow

1. Read the target repository's local instructions before dispatching work.
2. Use interactive Codex judgment to summarize the repository rules, planning basis, validation strategy, workstreams, dependencies, write scopes, and pending decisions.
3. Write any Dispatch Engine-generated plan file under `.dispatch/plans/` in the target repository.
4. Import the explicit plan into runtime state with `python scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json`.
5. Preview the coordinator launch with `python scripts/de.py run <repo> --dry-run`; omit `--provider` for the default Codex coordinator, or pass `--provider codex` or `--provider claude` explicitly.
6. Ask the user before worker execution when the plan contains pending decisions, high-risk surfaces, or parallel workstreams.
7. Start the coordinator with `python scripts/de.py run <repo> --detach` when interactive Codex should remain responsive; use foreground `de run` only for debugging or CI-style smoke checks.
8. Immediately create a host-layer heartbeat monitor for the current thread after every successful interactive detached launch. This is required, not optional, when the host supports thread wakeups. The default interval is 15 minutes.
9. Configure the heartbeat to read `status --json`, `events --since`, and `alerts --json`, report only material changes, request user input for decisions or blockers, and stop itself when the run reaches `completed`, `failed`, or `cancelled`.
10. If the host cannot create a heartbeat, state that the detached run is not proactively supervised in this chat and ask before continuing.
11. Monitor status through Codex-facing JSON/file surfaces, starting with `status --json`; use `events --since`, `alerts --json`, and `.dispatch/runs/` files for deltas, material alerts, and deeper inspection.
12. Resolve pending decisions explicitly after user approval with `resolve-decision`.
13. Record validation evidence before claiming a run is complete.

## Coordinator And Agent Protocol

Provider CLI processes are coordinators only. A coordinator may plan, dispatch,
monitor, review, summarize, request decisions, and write Dispatch Engine runtime
state under `.dispatch/`; it must not directly implement project-file changes.
Project implementation belongs to registered workers, reviewers, or validators.
Coordinator owns spawn decisions; Dispatch Engine owns the durable
observability contract. Coordinators may use provider-native spawn mechanisms
for workers, reviewers, and validators, but every spawned agent must be visible
through the same `.dispatch/` files.

Workers, reviewers, and validators must be registered before their output is
treated as valid. Worker output requires a durable JSON report under
`.dispatch/runs/<run-id>/reports/<agent-id>.json`; reviewer evidence belongs
under `.dispatch/runs/<run-id>/reviews/<agent-id>.json`; validator evidence
belongs under `.dispatch/runs/<run-id>/validation/<agent-id>.json`. Missing
reports, malformed reports, or worker changed files outside the assigned files
and allowed write roots are protocol violations. Prompt snapshots, reports,
logs, status records, and heartbeats for spawned agents live under:

```text
.dispatch/runs/<run-id>/agents/
.dispatch/runs/<run-id>/prompts/
.dispatch/runs/<run-id>/supervisors/
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/reviews/
.dispatch/runs/<run-id>/validation/
.dispatch/runs/<run-id>/logs/
.dispatch/runs/<run-id>/heartbeats/
```

Live `de run` registers `coordinator-001` with status `running`, then updates it
to `completed` or `failed` when the provider process exits. `de status` reads
these files to report coordinator provider/profile/status, agent counts by role
and status, active assignments, heartbeat counts, pending decisions, and
protocol violations. Lifecycle events include `coordinator.started`,
`coordinator.completed`, `coordinator.failed`, `agent.spawned`,
`agent.heartbeat`, `workstream.assigned`, `agent.completed`, `agent.failed`,
`protocol.violation`, and `decision.requested`.

## Packaging Rule

Before telling a user to install or copy this skill, verify that the runnable runtime is present under `scripts/` and that the basic CLI smoke checks pass:

```bash
python scripts/de.py --help
python scripts/de.py version
```

If runtime code has moved or been rebuilt elsewhere, copy or vendor the current runtime back into this skill directory before installation guidance.

Install by cloning or copying the complete skill root into
`$CODEX_HOME/skills/dispatch-engine`, or `~/.codex/skills/dispatch-engine` when
`CODEX_HOME` is unset. Do not split `SKILL.md` from `scripts/`, `references/`,
or `references/prompts/`; the runtime is intentionally bundled inside the skill
repo.

## Reference Files

- Read `references/operator-guide.md` when installing the skill or operating it against a target repo.
- Read `references/operator-flow.md` when supervising a run from interactive Codex.
- Read `references/heartbeat-observation.md` when configuring or explaining detached-run heartbeat observation.
- Read `specs/rfc-0015-codex-heartbeat-observation/` when changing detached-run observation, heartbeat wakeup guidance, Codex-facing status/actions, or decision-resolution surfaces.
- Read `references/event-protocol.md` when changing run-state or event-log behavior.
- Read `references/worker-protocol.md` when changing worker or reviewer adapters.
- Read `references/orchestrator-loop.md` when designing coordinator-spawned worker, reviewer, validator, evidence, and status/tail flows.
- Read `references/prompts/` when changing runtime prompt templates.
