---
language: en-US
audience: agent
doc_type: normative
---

# Review Validator Protocol

Use this reference when changing reviewer or validator evidence.

For workstream state and acceptance semantics, use
`references/workstream-acceptance-guidance.md` as the skill-first source of
truth.

## Source Of Truth

Reviewer and validator behavior is skill-first. Review judgment, acceptance semantics,
quality bars, and validation strategy belong in skills, references, and prompt
templates. Runtime code provides only durable report paths, mechanical report
validation, and status visibility.

The coordinator may spawn reviewers and validators through provider-native
mechanisms. Dispatch Engine does not launch them in this RFC. Their output is
valid evidence only after the agent is registered under
`.dispatch/runs/<run-id>/agents/` and a mechanically valid report is written.
Reviewer and validator records also carry normalized capability profiles:
`reviewer-standard` and `validator-standard` when omitted. They are expected to
remain read-only against project files unless the granted profile or a recorded
decision expands scope.

## Report Locations

```text
.dispatch/runs/<run-id>/
  reviews/<reviewer-agent-id>.json
  validation/<validator-agent-id>.json
  prompts/<agent-id>.md
  agents/<agent-id>.json
```

Reviewer reports belong under `reviews/`. Validator reports belong under
`validation/`. Worker reports remain under `reports/`.

## Reviewer Report

Reviewer reports include:

- `schema_version`
- `agent_id`
- `role`: `reviewer`
- `workstream`
- `status`: `accepted`, `changes_requested`, `blocked`, or `failed`
- `summary`
- `findings`
- `risks`
- `requested_changes`
- `validation_gaps`
- `recommendation`
- `capability_profile_id`
- `capabilities_exercised`
- `capability_escalations`

Allowed reviewer statuses are `accepted`, `changes_requested`, `blocked`, and
`failed`. Use the canonical field names above; do not substitute aliases for
`changes_requested` or `accepted` in durable reviewer reports.

Reviewer reports are acceptance evidence, not automated final acceptance. A
reviewer may recommend continuation, changes, blocking, or escalation. The
coordinator/operator combines reviewer evidence with worker evidence, validator
evidence, and decision/blocker state before marking a workstream accepted. The
runtime must not reinterpret review quality beyond report shape and status
consistency.

## Validator Report

Validator reports include:

- `schema_version`
- `agent_id`
- `role`: `validator`
- `workstream`
- `status`: `passed`, `failed`, `blocked`, or `skipped`
- `summary`
- `command`
- `output_summary`
- `artifacts`
- `not_run_reason`
- `capability_profile_id`
- `capabilities_exercised`
- `capability_escalations`

For `passed`, `failed`, or `blocked`, a validator report must include command
evidence, output summary, and at least one artifact reference. `artifacts`
must be an array. For `skipped`, it must include a specific `not_run_reason`
string.

Validators must not use `status: "completed"` for new reports. Version 1
runtime validation accepts that value only as a narrow compatibility alias for
`passed` when the report identity matches, aggregate evidence is complete,
every structured `validation[]` item is passed or skipped with evidence, and
`scope_check` has no failures or violations.

Optional structured evidence may include:

- `validated_agent_id`: worker or reviewer id being validated
- `validation[]`: check objects with `command`, `status`, and `evidence`
- `scope_check`: status, violations, changed files, and allowed write roots
- `risks`
- `completed_at`

Structured evidence supplements the aggregate `command`, `output_summary`, and
`artifacts` fields; it does not replace them for non-skipped reports.

## Protocol Violations

Runtime may emit conservative violations for mechanical problems:

- missing reviewer or validator report for a completed registered agent
- malformed reviewer report
- validator report JSON that cannot be parsed
- missing validator fields, invalid field types, identity mismatch, or illegal validator status
- validator report missing required command, output, artifact, or skip evidence
- validator report evidence that contradicts a passed or compatibility-normalized status
- reported capability use that exceeds the granted profile without a decision id
- workstream marked accepted, implemented, or completed without registered evidence

For validator report schema failures, `status --json` may include
`next_actions[]` items with `type: "repair_report_schema"`, the validator
`agent_id`, `report_path`, diagnostic code, and any suggested canonical status.
Coordinators should satisfy those actions through a recorded repair helper or
repair worker with its own prompt/report evidence. They should not silently
hand-edit malformed reviewer or validator JSON without a durable repair record.

Runtime must not decide whether a review finding is correct, whether a command
is sufficient for acceptance, or whether a residual risk is acceptable.
