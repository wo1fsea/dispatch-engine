---
language: en-US
audience: agent
doc_type: normative
---

# Decision Blocker Protocol

Use this reference when a coordinator, worker, reviewer, or validator reaches a
decision point, blocker, or requested scope change during a Dispatch Engine run.

## Principle

Dispatch Engine is skill-first and runtime-when-necessary. Agents use skill and
reference guidance to decide when to stop, ask, continue, narrow scope, or
escalate. Runtime helpers only store durable records under `.dispatch/`, expose
queryable state, and report mechanical validation signals such as unresolved
blockers.

Runtime must not infer the right product choice, broaden scope on its own, or
act as an approval workflow.

## When To Request A Decision

Request a decision before continuing when any of these are true:

- The work would broaden the accepted write scope, validation scope, or product
  behavior.
- Two instructions conflict and the safer interpretation would leave the task
  incomplete.
- A worker or reviewer found a blocker that needs operator or interactive Codex
  judgment.
- A validation result is ambiguous enough that retrying, skipping, or changing
  the command is a real choice.
- A dependency, shared file, or parallel workstream conflict needs an explicit
  sequencing or ownership call.
- The next action would discard, overwrite, or reinterpret another worker's
  existing changes.
- The next action requires a capability outside the granted
  `capability_profile`, including broader `network_access`, `package_install`,
  `dependency_resolution`, `docker_socket`, `service_start`, `test_execution`,
  `runtime_state_write`, or `github_issue_create`.
- A workstream needs GitHub issue evidence but has `network_access: none` and
  no recorded read-only grant or local-only evidence strategy. Running
  `gh issue view` in that state is capability overreach.

When in doubt, narrow the immediate work, record the blocker, and ask the
operator rather than guessing.

## Roles

Coordinators:

- Record decision requests and blockers when work cannot proceed safely.
- Keep project-file implementation delegated to registered workers.
- Resume workstreams only after the relevant decision or blocker is resolved.
- Summarize the exact choice needed, the reason, and the blocked workstream.

Workers:

- Stop and report a blocker when the assigned scope is insufficient, unsafe, or
  contradicted by current repo state.
- Do not silently expand assigned files, validation commands, or acceptance
  criteria.
- Do not silently use a denied or broader capability. Record the capability,
  requested mode, reason, risk, and validation expectation before continuing.
- If GitHub issue evidence is requested without network access, either stop for
  a read-only `network_access` decision or report an explicit local-only
  evidence strategy before any `gh issue view` command is used.
- Include blocker ids in worker reports when they paused work.

Reviewers and validators:

- Record or request a decision when acceptance depends on a product or operator
  judgment rather than a mechanical finding.
- Treat unresolved blockers as a validation signal, not as a failure to invent a
  plan.

Interactive Codex / operator:

- Remains the decision maker.
- Records the resolution so future status, tail, and continuation work can see
  why the run proceeded.
- May make an autonomous technical decision only after the same pending
  technical choice has remained unresolved across four consecutive heartbeat
  checks. Outer interactive Codex plus heartbeat observation owns this
  eligibility judgment. Autonomous resolution must be conservative,
  reversible, inside the approved objective, and recorded with
  `resolve-decision --autonomous-technical`, which uses actor
  `interactive-codex-autonomous`.

## Runtime Records

Decision requests are append-only records in:

```text
.dispatch/runs/<run-id>/decisions.jsonl
```

Latest decision records include:

- `schema_version`
- `decision_id` and compatibility `id`
- `status`: `pending` or `resolved`
- `question`
- optional `reason`
- optional `workstream`
- timestamps
- `actor`
- `resolution`, `resolved_at`, and `resolved_by` once resolved
- `resolution_mode: autonomous_technical` and `autonomous_decision` metadata
  when resolved through the autonomous technical fallback

For autonomous technical resolutions, `decisions.jsonl` is the source of truth.
The runtime persists the supplied metadata, validates mechanical invariants, and
emits the normal `decision.resolved` event. It does not judge whether the
decision is truly technical, choose an option, or bypass excluded decision
categories.

Blockers are append-only records in:

```text
.dispatch/runs/<run-id>/blockers.jsonl
```

Latest blocker records include:

- `schema_version`
- `blocker_id` and compatibility `id`
- `status`: `open`, `blocked`, or `resolved`
- `summary`
- `severity`
- optional `workstream`
- timestamps
- `actor`
- `resolution`, `resolved_at`, and `resolved_by` once resolved

Append new records to correct or resolve state. Do not rewrite JSONL history
unless the entire run is intentionally discarded.

## Events

Decision and blocker helpers emit run events for tail visibility:

- `decision.requested`
- `decision.resolved`
- `blocker.recorded`
- `blocker.resolved`

Events are observability, not the source of decision truth. The latest folded
records in `decisions.jsonl` and `blockers.jsonl` are the query surface.
Capability escalation uses the same decision/blocker records. Status may also
surface `capability.profile.granted`, `capability.escalation.requested`,
`capability.escalation.resolved`, and `capability.violation` events as audit
signals when helpers or coordinators emit them.

## Validation Signal

Unresolved blockers are mechanical validation state. A run with unresolved
blockers should report:

- `status: blocked` from the decision/blocker validation helper.
- A non-zero unresolved blocker count in status output.
- The latest blocker records so the coordinator or operator can resolve them.

Pending decisions are not automatically resolved by validation. They remain
pending until a recorded resolution exists.

## Autonomous Technical Decision Fallback

Heartbeat observation may encounter a technical decision that blocks progress
while the user is away. After four consecutive heartbeat checks with the same
pending technical decision still unresolved, interactive Codex may select a
technical option and continue work.

This fallback is allowed only for technical implementation choices such as
internal API shape, adapter strategy, test organization, validation retry
strategy, or similarly reversible engineering tradeoffs. It is not allowed for
product behavior, security/privacy posture, deployment, credentials,
destructive data actions, legal/financial judgments, or broadening the user's
business objective.

Autonomous resolutions must be recorded in `decisions.jsonl` through
`resolve-decision` with Codex-facing autonomous metadata:

- `--autonomous-technical`
- `--unanswered-heartbeats <count>` with a minimum of `4`
- `--autonomous-rationale <text>`
- `--validation-expected <command>` for each expected check
- optional heartbeat context such as `--heartbeat-interval-minutes`,
  `--first-seen-heartbeat-id`, and `--last-seen-heartbeat-id`
- `resolved_by` / `actor`: `interactive-codex-autonomous`
- selected option id
- `resolution_mode: autonomous_technical`
- `autonomous_decision` metadata asserting technical scope, conservative and
  reversible choice, approved objective, excluded categories, rationale, and
  validation expectations

`status --json` may include an `autonomous_decisions` count and compact records
for final-report convenience. Use that summary for reporting, but read
`decisions.jsonl` when durable detail or audit history matters.

At final completion, interactive Codex must report all autonomous technical
decisions together, even if the implementation succeeded.
