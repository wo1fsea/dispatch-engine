---
spec_id: rfc-0019-validator-report-schema-diagnostics
language: en-US
audience: agent
doc_type: spec
status: planned
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/2
---

# Validator Report Schema Diagnostics Tech Spec

Product spec: `./PRODUCT.md`

## Design Boundary

This RFC is a narrow repair to the rfc-0009 validator report protocol. Runtime
changes are allowed only for mechanical schema validation, diagnostics,
regression coverage, and `de status --json` next-action clarity. Review and
validation judgment remain skill-first.

Do not change worker or reviewer report behavior except where shared diagnostic
helpers need clearer names.

## Canonical Schema

Validator report version 1 remains:

```json
{
  "schema_version": 1,
  "agent_id": "validator-010",
  "role": "validator",
  "workstream": "04-cli-run-loop-validation",
  "status": "passed",
  "summary": "Validation passed.",
  "command": "PYTHONPATH=scripts python3 -m unittest discover -s tests",
  "output_summary": "All tests passed.",
  "artifacts": [".dispatch/runs/<run-id>/validation/validator-010.stdout.log"],
  "not_run_reason": ""
}
```

Allowed canonical statuses:

- `passed`
- `failed`
- `blocked`
- `skipped`

Optional structured evidence fields:

- `validated_agent_id`: worker or reviewer id being validated
- `validation`: array of check objects
- `scope_check`: object containing status, violations, changed files, and
  allowed write roots
- `risks`: array
- `completed_at`: timestamp

`validation[]` item shape:

```json
{
  "command": "uv lock --check",
  "status": "passed",
  "evidence": "Resolved 24 packages."
}
```

Allowed `validation[]` item statuses are `passed`, `failed`, `blocked`, and
`skipped`.

## Compatibility Rule

Accept `status: "completed"` as a version 1 compatibility alias for
`normalized_status: "passed"` only when all of these are true:

- `schema_version` is `1`.
- Required identity fields match the registered validator.
- `summary`, `command`, `output_summary`, and `artifacts` satisfy the normal
  non-skipped evidence requirement.
- Every structured `validation[]` item has `status: "passed"` or `status:
  "skipped"` with evidence explaining the skip.
- `scope_check.status` is absent or `passed`.
- `scope_check.violations` is absent or an empty array.

If any condition fails, the report is invalid. The diagnostic should still name
`completed` as a compatibility value and identify the failed compatibility
condition.

The runtime may expose normalized status as diagnostic metadata, for example:

```json
{
  "agent_id": "validator-010",
  "role": "validator",
  "report_path": ".dispatch/runs/<run-id>/validation/validator-010.json",
  "status": "completed",
  "normalized_status": "passed",
  "diagnostics": [
    {
      "severity": "warning",
      "code": "compat_validator_status_completed",
      "field": "status",
      "actual": "completed",
      "normalized_to": "passed"
    }
  ]
}
```

Warnings are not protocol violations. Errors are protocol violations.

## Diagnostic Contract

Add structured diagnostic helpers for validator reports. Protocol violations
may keep the existing top-level event shape, but `details` must be specific.

Required error codes:

- `missing_validator_report`
- `malformed_validator_json`
- `missing_validator_fields`
- `invalid_validator_field_type`
- `invalid_validator_status`
- `missing_validation_evidence`
- `inconsistent_validation_evidence`
- `validator_identity_mismatch`

Required diagnostic fields where applicable:

- `agent_id`
- `report_path`
- `field`
- `actual`
- `expected`
- `allowed`
- `missing_fields`
- `suggested_status`
- `compatibility_rule`
- `evidence_mode`

Examples:

```json
{
  "violation": "invalid_validator_status",
  "agent_id": "validator-010",
  "details": {
    "report_path": ".dispatch/runs/<run-id>/validation/validator-010.json",
    "field": "status",
    "actual": "complete",
    "allowed": ["passed", "failed", "blocked", "skipped"],
    "suggested_status": "passed"
  }
}
```

```json
{
  "violation": "missing_validation_evidence",
  "agent_id": "validator-010",
  "details": {
    "report_path": ".dispatch/runs/<run-id>/validation/validator-010.json",
    "missing_fields": ["output_summary", "artifacts"],
    "evidence_mode": "non_skipped_validator"
  }
}
```

## Minimal Runtime / Status Changes

1. Split validator validation from the shared reviewer/validator path enough to
   produce validator-specific diagnostics.
2. Normalize `completed` to `passed` only through the compatibility rule above.
3. Preserve existing report files; do not rewrite reports during validation.
4. Include diagnostic details in detected protocol violations.
5. Add or refine `status --json` `next_actions` so report-schema failures
   produce a concrete action:

```json
{
  "type": "repair_report_schema",
  "agent_id": "validator-010",
  "role": "validator",
  "report_path": ".dispatch/runs/<run-id>/validation/validator-010.json",
  "diagnostic": "invalid_validator_status",
  "suggested_status": "passed"
}
```

6. Keep the broader `repair_protocol_violations` action only as a fallback
   summary when specific actions are unavailable.

## Regression Fixture

Add a focused fixture under tests, for example:

```text
tests/fixtures/validator_reports/validator-010-useful-completed.json
```

The fixture should be a sanitized copy of the alpha-kitchen dogfood report:

- `schema_version: 1`
- `agent_id: "validator-010"`
- `role: "validator"`
- `workstream: "04-cli-run-loop-validation"`
- `validated_agent_id: "worker-013"`
- `status: "completed"`
- non-empty `summary`
- non-empty `command`
- non-empty `output_summary`
- `validation[]` with passed checks
- `scope_check.status: "passed"`
- `scope_check.violations: []`
- non-empty `artifacts`
- `risks[]`
- `completed_at`

Required tests:

- fixture with registered completed validator returns no protocol violations
  and exposes normalized status diagnostics if implemented.
- same fixture with one `validation[].status: "failed"` returns
  `inconsistent_validation_evidence`.
- same fixture without `output_summary` returns
  `missing_validation_evidence`.
- same fixture with `status: "complete"` returns
  `invalid_validator_status`.
- `de status --json` on a temp run with an invalid validator report includes
  `repair_report_schema` next action with `agent_id`, `report_path`, and the
  diagnostic code.

## Workstreams

1. `01-schema-diagnostics`: validator schema helpers, compatibility rule, and
   status next-action detail.
2. `02-regression-fixture`: fixture and focused tests from issue #2.
3. `03-prompts-docs-validation`: prompt/reference guidance and validation
   checks.

## Validation

Implementation validation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
rg -n "completed|passed|missing_validation_evidence|repair_report_schema|validation\\[\\]" references tests scripts specs/rfc-0019-validator-report-schema-diagnostics
git diff --check
```

Spec-only validation:

```bash
rg -n "validator-010|completed|repair_report_schema|missing_validation_evidence|inconsistent_validation_evidence" specs/rfc-0019-validator-report-schema-diagnostics
git diff --check -- specs/rfc-0019-validator-report-schema-diagnostics
```
