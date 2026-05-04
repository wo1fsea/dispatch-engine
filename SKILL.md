---
name: dispatch-engine
description: Runtime-backed Codex skill for supervising repo-native agent work. Use when a user wants interactive Codex to read a repository's own planning conventions, prepare an explicit dispatch plan, import that plan into durable Dispatch Engine state, monitor agent workers/reviewers, resolve pending decisions, or package the bundled runtime for direct skill installation.
---

# Dispatch Engine

Use this skill to operate the bundled Dispatch Engine runtime from a repository or task context.

Dispatch Engine is a skill-first project: the skill root contains the operator instructions, the runnable local CLI, runtime modules, and reference protocols. A user should be able to clone or copy this directory into their Codex skills directory and have the runtime available through the bundled scripts.

Project GitHub repository: `https://github.com/wo1fsea/dispatch-engine`.
Framework, skill, runtime, protocol, heartbeat, prompt, status, or process
blocker issues encountered while using this skill or `de` must be proactively
reported to `https://github.com/wo1fsea/dispatch-engine/issues`. Use
`references/issue-reporting-protocol.md` before filing or drafting the issue.

The bundled `de` CLI is a Codex-facing machine interface, not the human user
interface. Humans talk to interactive Codex; interactive Codex calls `de`,
reads JSON/file state, and explains progress or decisions in conversation.

For install, target repo quickstart, progress watching, git ignore guidance,
and troubleshooting, read `references/operator-guide.md`. For detached-run
heartbeat guidance, read `references/heartbeat-observation.md`. For proactive
GitHub issue reporting, read `references/issue-reporting-protocol.md`.

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
python scripts/de.py cancel <repo> --run-id <run-id> --reason "User asked to stop" --json
python scripts/de.py stop <repo> --run-id <run-id> --reason "User asked to stop" --json
python scripts/de.py resolve-decision <repo> --id <decision-id> --option <option-id> --json
python scripts/de.py resolve-decision <repo> --id <decision-id> --option <option-id> \
  --autonomous-technical --unanswered-heartbeats 4 \
  --autonomous-rationale "<why this is conservative and reversible>" \
  --validation-expected "<validation command>" --json
python scripts/de.py resolve-protocol-violation <repo> --run-id <run-id> \
  --violation <name> --resolution superseded_by_validation \
  --rationale "<why this protocol issue is reviewed>" \
  --evidence "<validation or audit evidence>" --json
python scripts/de.py tail <repo>
```

`de run <repo>` launches the latest imported run's provider CLI coordinator in
the foreground. `de run <repo> --detach` starts a background supervisor and
returns immediately so interactive Codex can keep talking with the user while
`de status` and `de tail` expose progress. When `--provider` is omitted, the
runtime uses provider `codex` and launches a Codex CLI command shape based on
`codex exec --sandbox danger-full-access`. `--provider codex` selects the same
provider/profile explicitly. `--provider claude` launches a Claude CLI command
shape based on
`claude --dangerously-skip-permissions --permission-mode bypassPermissions -p`.

`de run <repo> --dry-run` renders the provider command and coordinator prompt
without starting Codex, Claude, or any other provider process, and without
writing run state. Dry-run output includes the resolved command, run id, state
directory, and coordinator prompt marker or preview.

`de cancel <repo>` is the canonical user-requested cancellation control for an
active run; `de stop <repo>` is a natural-language alias. Both support
`--run-id`, `--reason`, and `--json`, resolve the latest run by default, attempt
graceful process termination before escalation, preserve all `.dispatch/`
evidence, and mark the run plus active supervisor/coordinator/agent records
`cancelled` with the cancellation reason. Cancellation is distinct from
failure, and already-cancelled runs return idempotent success.

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
files, allowed write roots, granted capability profile, validation
expectations, escalation rules, and report path.

## Operating Flow

1. Read the target repository's local instructions before dispatching work.
2. Use interactive Codex judgment to summarize the repository rules, planning basis, validation strategy, workstreams, dependencies, write scopes, and pending decisions.
3. Write any Dispatch Engine-generated plan file under `.dispatch/plans/` in the target repository.
4. Import the explicit plan into runtime state with `python scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json`.
5. Preview the coordinator launch with `python scripts/de.py run <repo> --dry-run`; omit `--provider` for the default Codex coordinator, or pass `--provider codex` or `--provider claude` explicitly.
6. Ask the user before worker execution when the plan contains pending decisions, high-risk surfaces, or parallel workstreams.
7. Start the coordinator with `python scripts/de.py run <repo> --detach` when interactive Codex should remain responsive; use foreground `de run` only for debugging or CI-style smoke checks.
8. Immediately create a host-layer heartbeat monitor for the current thread after every successful interactive detached launch. This is required, not optional, when the host supports thread wakeups. The default interval is 15 minutes.
9. Configure the heartbeat to read `status --json`, `events --since`, and `alerts --json`, report only material changes, request user input for decisions or blockers, apply the four-heartbeat autonomous technical-decision fallback when allowed, and stop itself when the run reaches `completed`, `failed`, or `cancelled`.
10. If the host cannot create a heartbeat, state that the detached run is not proactively supervised in this chat and ask before continuing.
11. Monitor status through Codex-facing JSON/file surfaces, starting with `status --json`; use `events --since`, `alerts --json`, and `.dispatch/runs/` files for deltas, material alerts, and deeper inspection.
12. If the user asks to stop a run, call
    `python scripts/de.py cancel <repo> --run-id <run-id> --reason "<user-facing reason>" --json`,
    then read `status --json`, `events --since`, and `alerts --json` before
    summarizing the terminal cancelled state. Use `stop` only as an alias when
    natural language makes it clearer; keep `cancel` canonical in docs and
    automation.
13. Resolve pending decisions explicitly after user approval with
    `resolve-decision`. If the same technical decision remains unresolved after
    four consecutive heartbeat checks, interactive Codex plus the heartbeat
    owns the eligibility judgment and may choose a conservative, reversible
    option. Record that choice with `resolve-decision --autonomous-technical`;
    the runtime validates only the supplied metadata invariants, defaults the
    actor to `interactive-codex-autonomous`, appends the source-of-truth record
    to `.dispatch/runs/<run-id>/decisions.jsonl`, and exposes a convenience
    `status --json` `autonomous_decisions` summary.
14. When protocol violations are reviewed, accepted with concerns, judged false
    positive, or superseded by later validation, record the audit judgment with
    `resolve-protocol-violation`. This appends
    `.dispatch/runs/<run-id>/protocol-resolutions.jsonl`, preserves the
    original violation evidence, affects unresolved status/alert overlays only,
    and never rewrites terminal run state or future worker capability grants.
15. Record validation evidence before claiming a run is complete. The final report must list every autonomous technical decision made during the run.
16. When this skill, `de`, the coordinator protocol, heartbeat guidance,
    status/alert/event surfaces, prompt templates, or any Dispatch
    Engine-owned process creates a framework problem or process blocker, follow
    `references/issue-reporting-protocol.md` and proactively file or prepare a
    GitHub issue against `https://github.com/wo1fsea/dispatch-engine`.

## Coordinator And Agent Protocol

Provider CLI processes are coordinators only. Dispatch Engine launches the
coordinator with high provider permissions so it can spawn agents, install
dependencies, validate work, and inspect repo state. A coordinator may plan,
dispatch, monitor, review, summarize, request decisions, and write Dispatch
Engine runtime state under `.dispatch/`; it must not directly implement
project-file changes. Project implementation belongs to registered workers,
reviewers, or validators. Coordinator owns spawn decisions and decides worker
permission scope through assigned files, allowed write roots, normalized
capability profiles, and provider-native worker launch options. Dispatch
Engine owns the durable observability contract. Coordinators may use
provider-native spawn mechanisms for workers, reviewers, and validators, but
every spawned agent must be visible through the same `.dispatch/` files.
Provider Worker Launch requires actual provider-native spawn evidence or codex
CLI fallback evidence before `agent.spawned` or `running`; registration alone
is not launch evidence.

Workers, reviewers, and validators must be registered before their output is
treated as valid. Worker output requires a durable JSON report under
`.dispatch/runs/<run-id>/reports/<agent-id>.json`; reviewer evidence belongs
under `.dispatch/runs/<run-id>/reviews/<agent-id>.json`; validator evidence
belongs under `.dispatch/runs/<run-id>/validation/<agent-id>.json`. Missing
reports, malformed reports, or worker changed files outside the assigned files
and allowed write roots are protocol violations. Validator report statuses are
`passed`, `failed`, `blocked`, and `skipped`; do not use `completed` for
validator report status. Worker report statuses are `completed`,
`completed_with_concerns`, `blocked`, and `failed`; both completed statuses are
valid completion evidence when the worker report is otherwise valid. Prompt
snapshots, reports, logs, status records, and heartbeats for spawned agents
live under:

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

Every workstream and spawned agent carries a normalized `capability_profile`.
Omitted worker profiles default to `worker-standard`; reviewers default to
`reviewer-standard`; validators default to `validator-standard`. The initial
capability vocabulary is `network_access`, `package_install`,
`dependency_resolution`, `docker_socket`, `service_start`, `test_execution`,
`runtime_state_write`, and `github_issue_create`. Provider enforcement remains
provider-specific; Dispatch Engine owns the auditable state, prompt, report,
status, and protocol-violation contract. Worker reports should include
`capability_profile_id`, `capabilities_exercised`, and
`capability_escalations`; runtime helper-written reports default those fields,
and capability use beyond the grant is `capability_overreach` unless the
exercised item links a recorded decision id.
Imported workstreams may include `validation_warnings` when validation commands
look inconsistent with the normalized profile; coordinators should resolve
those warnings before dispatch by narrowing validation, requesting a decision,
or blocking the workstream.

Live `de run` registers `coordinator-001` with status `running`, then updates it
to `completed` or `failed` when the provider process exits. `de status` reads
these files to report coordinator provider/profile/status, agent counts by role
and status, active assignments, heartbeat counts, pending decisions,
autonomous decision summaries, capability profile summaries, and protocol
violations. Lifecycle events include
`coordinator.started`,
`coordinator.completed`, `coordinator.failed`, `agent.spawned`,
`agent.heartbeat`, `workstream.assigned`, `agent.completed`, `agent.failed`,
`protocol.violation`, `capability.profile.granted`,
`capability.escalation.requested`, `capability.escalation.resolved`,
`capability.violation`,
`decision.requested`, `run.cancel.requested`, `run.cancel.signal`, and
`run.cancel.completed`.

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
- Read `references/issue-reporting-protocol.md` when any Dispatch Engine framework, skill, runtime, protocol, prompt, status, heartbeat, or process blocker issue appears during use.
- Read `specs/rfc-0015-codex-heartbeat-observation/` when changing detached-run observation, heartbeat wakeup guidance, Codex-facing status/actions, or decision-resolution surfaces.
- Read `specs/rfc-0016-autonomous-decision-records/` when changing autonomous technical-decision records, `resolve-decision --autonomous-technical`, or `status --json` autonomous decision summaries.
- Read `specs/rfc-0018-agent-capability-profiles/` when changing workstream or agent capability profiles, profile prompt rendering, capability escalation, overreach diagnostics, or `status --json` `capability_profiles`.
- Read `references/event-protocol.md` when changing run-state or event-log behavior.
- Read `references/worker-protocol.md` when changing worker or reviewer adapters.
- Read `references/orchestrator-loop.md` when designing coordinator-spawned worker, reviewer, validator, evidence, and status/tail flows.
- Read `references/prompts/` when changing runtime prompt templates.
