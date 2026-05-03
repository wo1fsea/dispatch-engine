---
spec_id: rfc-0019-validator-report-schema-diagnostics
language: en-US
audience: mixed
doc_type: spec
status: planned
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/2
---

# Validator Report Schema Diagnostics Product Spec

## Summary

Issue #2 found a Dispatch Engine protocol gap during alpha-kitchen dogfood.
The validator evidence file existed at
`.dispatch/runs/20260502T091041837644Z/validation/validator-010.json` and
contained useful structured evidence: command summaries, per-check validation
items, scope-check results, artifacts, risks, and completion metadata.
`de status --json` still reported `malformed_validator_report` and suggested
the broad next action `repair_protocol_violations`.

Dispatch Engine should preserve the canonical validator report contract while
making useful schema failures actionable. A provider validator that writes
structured evidence should either be accepted through a narrow compatibility
path or receive diagnostics that name the exact field mismatch and the repair
needed.

## Goals / Non-goals

- Goal: Define exact validator report schema expectations for version 1.
- Goal: Accept the useful alpha-kitchen dogfood shape without reporting a
  malformed validator report when evidence is otherwise complete.
- Goal: Keep canonical validator statuses as `passed`, `failed`, `blocked`,
  and `skipped`.
- Goal: Add diagnostics that distinguish invalid status, missing fields,
  wrong field types, missing evidence, and inconsistent evidence.
- Goal: Add a regression fixture based on the dogfood
  `validator-010.json` shape.
- Goal: Tighten validator prompt/reference guidance so future validators emit
  canonical reports directly.
- Non-goal: Launch validators through Dispatch Engine.
- Non-goal: Change reviewer or worker report schemas.
- Non-goal: Make runtime decide whether a validation command was sufficient
  for product acceptance.
- Non-goal: Add a general schema migration framework.

## User Outcome

When a dogfood run produces validator evidence that is structurally useful,
the operator sees one of two outcomes:

1. The report is accepted as valid validator evidence, with any compatibility
   normalization exposed as a warning or diagnostic detail.
2. The report remains invalid, but `de status --json` identifies the exact
   field, expected value, actual value, and suggested repair.

The operator should not have to inspect runtime code to learn why a validator
report is malformed.

## Behavior Invariants

1. Validator reports still live under
   `.dispatch/runs/<run-id>/validation/<validator-agent-id>.json`.
2. A validator report is considered for evidence only after the validator is
   registered under `.dispatch/runs/<run-id>/agents/`.
3. Canonical validator status values remain `passed`, `failed`, `blocked`, and
   `skipped`.
4. `status: "completed"` is not canonical, but version 1 validator reports may
   normalize it to `passed` only when the report has successful validation
   evidence and no failed or blocked check evidence.
5. Missing or unusable evidence remains a protocol violation.
6. Diagnostics must be structured enough for `de status --json` and heartbeat
   observers to recommend a concrete repair.
7. Prompt and reference guidance should prevent future validators from using
   `completed` for validator report status.

## Validator Report Expectations

Required top-level fields:

- `schema_version`: `1`
- `agent_id`: string matching the registered validator
- `role`: `validator`
- `workstream`: string matching the registered validator assignment
- `status`: canonical status, or compatibility value `completed` when
  normalization rules pass
- `summary`: non-empty string
- `artifacts`: array of artifact path strings

Evidence requirements:

- For canonical `passed`, `failed`, or `blocked`, the report must include
  non-empty `command`, non-empty `output_summary`, and at least one artifact.
- For canonical `skipped`, the report must include a specific
  `not_run_reason`.
- A structured `validation` array may supplement or explain aggregate
  command/output evidence. Each item should include `command`, `status`, and
  `evidence`.
- A `scope_check` object may supplement evidence. When present, a non-empty
  `violations` array is inconsistent with `passed` or normalized `completed`.

Compatibility expectation:

- The alpha-kitchen shape with `status: "completed"`, successful
  `validation[]`, successful `scope_check`, non-empty `command`,
  `output_summary`, and `artifacts` should be accepted as normalized
  `passed`, not reported as `malformed_validator_report`.

## Acceptance Criteria

1. A regression fixture based on alpha-kitchen
   `validator-010.json` validates without protocol violations.
2. The fixture preserves the useful fields `validated_agent_id`,
   `validation`, `scope_check`, `artifacts`, `risks`, and `completed_at`.
3. A validator report with `status: "completed"` and failed validation item
   remains invalid with an actionable diagnostic.
4. A validator report with an unknown status reports an
   `invalid_validator_status` diagnostic with allowed statuses and a suggested
   repair when possible.
5. A validator report missing command evidence reports
   `missing_validation_evidence` with exact missing field names.
6. `de status --json` next actions use a specific report repair action for
   report-schema failures instead of only the broad
   `repair_protocol_violations` action.
7. Validator prompt/reference guidance shows the canonical JSON shape and says
   not to use `completed` as validator status.
