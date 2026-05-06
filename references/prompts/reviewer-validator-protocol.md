---
language: en-US
audience: agent
doc_type: prompt-template
---

# Reviewer And Validator Terminal Evidence Protocol

This shared guidance is the source of truth for review and validation workers
when a workstream needs terminal evidence.

## Terminal Report Requirement

- Reviewers and validators must write a terminal report before their workstream
  can be accepted.
- A validator terminal report uses `status: "passed"`, `"failed"`,
  `"blocked"`, or `"skipped"` under `.dispatch/runs/<run-id>/validation/`.
- A non-skipped validator terminal report must include command evidence,
  output summary, and non-empty `artifacts`; missing any of those fields is
  `missing_validation_evidence` and is not clean acceptance evidence.
- A reviewer terminal report uses `status: "accepted"`,
  `"changes_requested"`, `"blocked"`, or `"failed"` under
  `.dispatch/runs/<run-id>/reviews/`.
- If validation cannot finish, write a blocked, failed, or skipped terminal
  report with the reason and available evidence instead of leaving only logs,
  stdout, or a stale heartbeat.
- If validation passed but artifact references were omitted, repair the
  validator report through durable repair evidence or rerun validation and
  record artifact references; do not treat the report as cleanly passed.
- If the run is cancelled before validation completes, the missing terminal
  report remains visible as `incomplete_validation_evidence`; do not describe
  the workstream as accepted.
- If a running reviewer or validator has no fresh heartbeat and no terminal
  report, status and alerts surface `stale_validation_worker_without_report`.

## Coordinator Handling

- A coordinator may wait only while fresh heartbeat or provider evidence shows
  progress.
- When stale validation evidence appears, the next action is to inspect the
  provider session, wait with evidence, cancel with user approval, or rerun
  validation and record a terminal validator report.
- Do not repair missing review or validation evidence by editing the report by
  hand without a durable repair worker or validator record.
