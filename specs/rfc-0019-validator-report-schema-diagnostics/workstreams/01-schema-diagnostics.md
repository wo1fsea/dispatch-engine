---
spec_id: rfc-0019-validator-report-schema-diagnostics
workstream_id: 01-schema-diagnostics
language: en-US
audience: agent
doc_type: workstream
status: planned
owner: TBD
created: 2026-05-03
updated: 2026-05-03
depends_on:
  - rfc-0009-review-validator-report-protocol
---

# Schema Diagnostics

## Scope

Implement validator-specific schema diagnostics, the narrow `completed` to
`passed` compatibility rule, and clearer status next actions.

## Files

Expected implementation surfaces:

- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/state.py`
- focused tests under `tests/`

Do not change worker or reviewer report semantics except for shared diagnostic
helpers needed by validator validation.

## Requirements

- Keep canonical validator statuses as `passed`, `failed`, `blocked`, and
  `skipped`.
- Accept `status: "completed"` only when it satisfies the compatibility rule
  in `TECH.md`.
- Preserve validator report files; validation must not rewrite reports.
- Return structured diagnostic details for missing fields, invalid status,
  wrong field type, missing evidence, inconsistent evidence, identity mismatch,
  and malformed JSON.
- Include `report_path`, `agent_id`, expected values, actual values, and
  suggested repair where applicable.
- Add `de status --json` `next_actions[]` items with
  `type: "repair_report_schema"` for report-schema failures.
- Keep broad `repair_protocol_violations` only as a fallback summary.

## Acceptance Criteria

- Useful `completed` validator reports are no longer surfaced as
  `malformed_validator_report`.
- Unknown statuses produce `invalid_validator_status`.
- Missing aggregate evidence produces `missing_validation_evidence` with exact
  missing field names.
- Failed structured validation evidence under normalized `completed` produces
  `inconsistent_validation_evidence`.
- Status JSON includes enough detail for a heartbeat observer to tell the
  operator what to repair.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
python3 scripts/de.py status --help
git diff --check
```
