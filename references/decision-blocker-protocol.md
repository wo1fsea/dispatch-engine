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

## Validation Signal

Unresolved blockers are mechanical validation state. A run with unresolved
blockers should report:

- `status: blocked` from the decision/blocker validation helper.
- A non-zero unresolved blocker count in status output.
- The latest blocker records so the coordinator or operator can resolve them.

Pending decisions are not automatically resolved by validation. They remain
pending until a recorded resolution exists.
