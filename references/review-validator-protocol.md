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

For `passed`, `failed`, or `blocked`, a validator report must include command
evidence, output summary, and at least one artifact reference. For `skipped`,
it must include a specific not-run reason.

## Protocol Violations

Runtime may emit conservative violations for mechanical problems:

- missing reviewer or validator report for a completed registered agent
- malformed reviewer or validator report
- illegal reviewer or validator status
- validator report missing required evidence
- workstream marked accepted, implemented, or completed without registered evidence

Runtime must not decide whether a review finding is correct, whether a command
is sufficient for acceptance, or whether a residual risk is acceptable.
