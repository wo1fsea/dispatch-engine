---
spec_id: rfc-0019-validator-report-schema-diagnostics
workstream_id: 02-regression-fixture
language: en-US
audience: agent
doc_type: workstream
status: planned
owner: TBD
created: 2026-05-03
updated: 2026-05-03
depends_on:
  - 01-schema-diagnostics
---

# Regression Fixture

## Scope

Add a focused regression fixture based on GitHub issue #2 and the
alpha-kitchen dogfood report
`.dispatch/runs/20260502T091041837644Z/validation/validator-010.json`.

## Files

Expected implementation surfaces:

- `tests/fixtures/validator_reports/validator-010-useful-completed.json`
- focused tests under `tests/`

The fixture should be sanitized but preserve the schema shape that triggered
the issue.

## Fixture Requirements

The fixture must include:

- `schema_version: 1`
- `agent_id: "validator-010"`
- `role: "validator"`
- `workstream: "04-cli-run-loop-validation"`
- `validated_agent_id: "worker-013"`
- `status: "completed"`
- non-empty `summary`
- non-empty `command`
- non-empty `output_summary`
- `validation[]` with check objects containing `command`, `status`, and
  `evidence`
- `scope_check.status: "passed"`
- `scope_check.violations: []`
- non-empty `artifacts`
- `risks[]`
- `completed_at`

## Test Cases

- Registered completed validator plus fixture produces no protocol violations.
- Fixture with one failed validation item produces
  `inconsistent_validation_evidence`.
- Fixture without `output_summary` produces `missing_validation_evidence`.
- Fixture with `status: "complete"` produces `invalid_validator_status`.
- Temp run status with invalid fixture includes `repair_report_schema` in
  `next_actions`.

## Acceptance Criteria

- The original dogfood evidence shape is represented in tests.
- The test fails against the current malformed-only behavior before
  implementation.
- The fixture protects the compatibility rule from future regressions.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg -n "validator-010-useful-completed|inconsistent_validation_evidence|repair_report_schema" tests specs/rfc-0019-validator-report-schema-diagnostics
git diff --check
```
