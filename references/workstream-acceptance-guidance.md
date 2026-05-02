---
language: en-US
audience: agent
doc_type: normative
---

# Workstream Acceptance Guidance

Use this reference when deciding whether a Dispatch Engine workstream is
implemented, accepted, needs changes, blocked, or failed.

## Principle

Dispatch Engine is skill-first and runtime-when-necessary. Acceptance judgment
belongs in coordinator, reviewer, validator, operator, and interactive Codex
guidance. Runtime code stores evidence, exposes status, and detects mechanical
contradictions only.

Do not implement a scheduler, transition engine, or automated acceptance engine
from this guidance.

## Evidence Paths

Workstream evidence is cumulative. A later evidence type does not erase earlier
evidence, and a report from one role must not impersonate another role.

- Worker evidence lives under `.dispatch/runs/<run-id>/reports/`.
- Reviewer evidence lives under `.dispatch/runs/<run-id>/reviews/`.
- Validator evidence lives under `.dispatch/runs/<run-id>/validation/`.
- Decision and blocker evidence lives in `.dispatch/runs/<run-id>/decisions.jsonl`
  and `.dispatch/runs/<run-id>/blockers.jsonl`.
- Agent registration evidence lives under `.dispatch/runs/<run-id>/agents/`.

Valid implementation evidence requires a registered worker, reviewer, or
validator with an assigned workstream and a mechanically valid report. A
coordinator report is not implementation evidence.

## State Meanings

- `planned`: Imported from an explicit plan and not yet assigned.
- `assigned`: A registered agent has been assigned, but implementation evidence
  has not completed.
- `implementing`: A worker is actively changing or preparing scoped files.
- `implemented`: Worker evidence exists and reports completed implementation,
  but review and validation acceptance are not complete.
- `reviewing`: A reviewer is inspecting worker evidence, changed files, risks,
  validation gaps, and acceptance criteria.
- `needs-fix`: A reviewer requested changes, or the coordinator determined the
  work should return to a worker before acceptance.
- `validating`: A validator is running or recording declared validation evidence.
- `accepted`: The workstream has enough worker, reviewer, and validation or
  explicit decision evidence for the coordinator/operator to treat it as done.
- `blocked`: Work cannot safely proceed without a recorded decision, blocker
  resolution, dependency completion, or operator/coordinator call.
- `failed`: The workstream cannot be completed in the current run without
  replanning or a material change in approach.

These states are guidance vocabulary. Runtime may display and count them, but it
must not infer semantic transitions beyond mechanical evidence checks.

## Acceptance Semantics

A workstream is accepted only when all required evidence for that workstream is
present and consistent:

- Worker report status is `completed` or `completed_with_concerns`.
- Reviewer report status is `accepted`, or a recorded coordinator/operator
  decision explicitly accepts residual review risk.
- Validator report status is `passed`, or a recorded coordinator/operator
  decision explicitly accepts skipped, blocked, partial, or unavailable
  validation.
- No unresolved blocker applies to the workstream.
- No pending decision is required for the acceptance call.
- Changed files and validation stay within the accepted plan scope, or a
  recorded decision expands that scope.

Reviewer acceptance is necessary review evidence, not automatic final
acceptance. Validator success is necessary validation evidence, not automatic
final acceptance. Final acceptance is a coordinator/operator judgment based on
the combined evidence.

## Changes Requested

Use `needs-fix` or reviewer status `changes_requested` when the evidence shows
the work is close enough to continue but should return to implementation before
acceptance:

- reviewer findings identify concrete defects or missing acceptance criteria
- validation gaps are actionable with the current scope
- worker evidence is incomplete but recoverable without replanning
- a small scope clarification is needed and can be resolved by decision before
  continuing

The coordinator should route the work back to a worker or request the missing
decision. Runtime should only surface the reports, status, and any mechanical
violations.

## Blocked

Use `blocked` when continuing would require guessing or crossing an ownership
boundary:

- unresolved blocker or pending decision affects the workstream
- the next step would broaden file scope, validation scope, or product behavior
- parallel work created a shared-file conflict that needs sequencing
- validation cannot be interpreted without operator judgment
- acceptance depends on accepting residual risk outside the reviewer or
  validator role

Blocked is not failure. It is a durable pause until a coordinator, operator, or
interactive Codex decision is recorded.

## Failed

Use `failed` when the current workstream path is no longer viable in this run:

- implementation failed and no narrow retry remains
- validation proves the approach is materially wrong
- required evidence cannot be produced without replanning
- the workstream repeatedly returns from review without a credible path to
  acceptance

Failure should include enough summary, risks, and validation evidence for the
coordinator/operator to decide whether to replan, split, abandon, or start a new
run.

## Coordinator And Operator Decisions

Escalate to a recorded decision instead of silently accepting when any of these
are true:

- reviewer accepts with non-trivial residual risks
- validator status is `skipped`, `blocked`, or `failed` but the work may still
  be acceptable for product reasons
- worker reports `completed_with_concerns`
- acceptance would depend on changing scope, dependencies, or validation
  commands
- a dependency is not accepted but the coordinator wants to proceed anyway
- another worker's changes would be overwritten, discarded, or reinterpreted

Decisions should name the workstream, the evidence being accepted or rejected,
the reason, and the next state.

## Runtime Boundary

Runtime may conservatively report mechanical issues:

- accepted, implemented, or completed workstreams with no registered evidence
- completed registered agents with missing or malformed reports
- illegal report status values
- validator reports missing command, output summary, artifacts, or a specific
  skip reason
- unresolved blockers and pending decisions

Runtime must not decide whether a finding is correct, whether validation is
sufficient, whether residual risk is acceptable, or whether a blocked
workstream should proceed.
