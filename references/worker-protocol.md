---
language: en-US
audience: agent
doc_type: normative
---

# Worker Protocol

Use this reference when changing worker or reviewer adapters.

## Source Of Truth

Workers and reviewers are assigned from imported dispatch plan state, not from a fresh runtime repository scan. Interactive Codex plus the skill prepares the plan; the runtime turns each imported workstream into adapter-neutral worker and reviewer prompts.

Generated worker prompts, reports, review records, and validation captures are non-project runtime content and stay under `.dispatch/runs/<run-id>/`.

Provider CLI processes launched through `de run` are coordinators, not
implementation agents. A coordinator may plan, dispatch, monitor, review,
summarize, request decisions, and write `.dispatch/` runtime state. It must not
directly implement project-file changes. Project implementation must be done by
registered workers, reviewers, or validators.

Coordinator owns spawn decisions; Dispatch Engine owns the durable
observability contract. A coordinator may spawn workers, reviewers, or
validators through provider-native mechanisms, and a future adapter may also
spawn agents, but both paths must use the same `.dispatch/` registration,
prompt snapshot, log, status, heartbeat, report, event, and violation contract.

## Coordinator Launch

The current coordinator launch surface supports live foreground execution and
dry-run rendering:

```bash
python3 scripts/de.py run <repo>
python3 scripts/de.py run <repo> --provider codex
python3 scripts/de.py run <repo> --provider claude
python3 scripts/de.py run <repo> --dry-run
python3 scripts/de.py run <repo> --provider codex --dry-run
python3 scripts/de.py run <repo> --provider claude --dry-run
```

Omitting `--provider` defaults to provider `codex`. Provider `codex` renders a
`codex exec --sandbox danger-full-access` command shape; provider `claude`
renders a
`claude --dangerously-skip-permissions --permission-mode bypassPermissions -p`
command shape. Dry-run renders the command and coordinator prompt without
launching a provider process or writing runtime state. Live launch writes a
coordinator prompt snapshot, stdout/stderr logs, a coordinator registry record,
and coordinator lifecycle events under `.dispatch/runs/<run-id>/`.

Dispatch Engine intentionally gives the coordinator high provider permissions.
The coordinator still remains coordinator-only: it must not directly implement
project-file changes. Worker, reviewer, and validator capability scope is
decided by the coordinator per assignment through assigned files, allowed write
roots, validation expectations, normalized `capability_profile` grants, and
provider-native worker launch options. Provider enforcement remains
provider-specific; Dispatch Engine owns the auditable state, prompt, report,
status, and protocol-violation contract.

## Agent Registration

Workers, reviewers, and validators must be registered in
`.dispatch/runs/<run-id>/agents/` before their output is accepted. Their
prompt snapshots, role-specific evidence, logs, and heartbeat streams belong
under:

```text
.dispatch/runs/<run-id>/prompts/
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/reviews/
.dispatch/runs/<run-id>/validation/
.dispatch/runs/<run-id>/logs/
.dispatch/runs/<run-id>/heartbeats/
```

Worker reports live under `reports/`, reviewer evidence lives under
`reviews/`, and validator evidence lives under `validation/`.

Every worker, reviewer, and validator registry record includes the granted
`capability_profile`, its source, and any decision ids that expanded it.
Omitted profiles normalize conservatively: `worker-standard`,
`reviewer-standard`, or `validator-standard`. Initial capability keys are
`network_access`, `package_install`, `dependency_resolution`, `docker_socket`,
`service_start`, `test_execution`, `runtime_state_write`, and
`github_issue_create`. Repo write scope remains the existing assigned-files and
allowed-write-roots contract, now embedded in the normalized profile.

Status readers use these files to report agent counts by role and status,
active assignments, heartbeat freshness, pending decisions, and
`protocol.violation` events. Lifecycle events include `agent.spawned`,
`agent.heartbeat`, `workstream.assigned`, `agent.completed`, and
`agent.failed`.

The helper-first worker baseline does not launch real worker provider
processes. It defines the durable contract adapters must use: register a worker,
render a prompt snapshot from `references/prompts/worker-protocol.md`, write the
worker report under `reports/`, and validate the report before accepting
implementation evidence.

Coordinator-spawned agents follow the same contract: the spawned agent is not
valid implementation evidence until it is registered, assigned, heartbeat/status
tracked, and represented by a valid worker report.

## Worker Input

A worker receives:

- target repository path
- objective
- one imported workstream
- relevant repository instructions summarized in the explicit plan
- allowed file scope from the explicit plan
- dependency and parallel group context
- validation expectations
- granted capability profile and escalation policy
- report path under `.dispatch/runs/<run-id>/reports/`
- a reminder that the worker is not alone in the codebase and must preserve
  unrelated changes

## Worker Output

A worker returns:

- status: `completed`, `completed_with_concerns`, `blocked`, or `failed`
- summary
- changed files
- validation evidence
- questions
- blockers
- residual risks
- `capability_profile_id`
- `capabilities_exercised`
- `capability_escalations`

Worker reports are JSON files with `schema_version`, `agent_id`, `role`,
`workstream`, `status`, `summary`, `changed_files`, `validation`, `questions`,
`blockers`, `risks`, `capability_profile_id`, `capabilities_exercised`, and
`capability_escalations`. A completed worker with a missing report, malformed
report, changed file outside assigned scope, or exercised capability broader
than the granted profile is a `protocol.violation`. Capability overreach is
allowed only when the exercised item links a recorded decision id.

## Reviewer Input

A reviewer receives:

- target repository path
- objective
- imported workstream
- worker report
- changed-file summary
- validation evidence available so far
- acceptance criteria from the plan

## Reviewer Output

A reviewer returns:

- status: `accepted`, `changes_requested`, `blocked`, or `failed`
- findings or residual risks
- validation gaps
- recommendation for coordinator continuation

## Rule

Each worker owns one workstream at a time. Parallel workers must be told they are not alone in the codebase and must avoid files outside their declared scope.

Agents must stop before using a denied or broader capability. They should record
the needed capability, requested mode, reason, risk, and validation expectation
as a blocker or decision request, then wait for the coordinator/operator to
approve, deny, narrow, or reassign the work.

Reviewer acceptance is a separate phase before a workstream is considered
accepted. A worker report alone is not completion evidence. Final acceptance is
a coordinator/operator judgment over worker, reviewer, validator, and
decision/blocker evidence.

A coordinator report alone is also not implementation evidence. Any project-file
change must be attributable to a registered worker, reviewer, or validator with
an assigned scope and durable report.
