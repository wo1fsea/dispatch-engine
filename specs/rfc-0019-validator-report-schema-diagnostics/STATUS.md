---
spec_id: rfc-0019-validator-report-schema-diagnostics
language: en-US
audience: agent
doc_type: status
status: ready-for-implementation
implementation: planned
validation: spec-only
coordinator: dispatch-engine
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/2
---

# Status

## Summary

Ready for implementation. This RFC defines the validator report schema
diagnostics needed after issue #2: keep canonical validator statuses as
`passed`, `failed`, `blocked`, and `skipped`; accept the useful dogfood
`status: "completed"` shape only through a narrow compatibility rule; add
structured diagnostics; add a regression fixture; and tighten validator prompt
guidance.

No runtime, docs, or tests outside this spec directory have been implemented by
this RFC authoring pass.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Schema diagnostics | planned | TBD | TBD | rfc-0009 | 2026-05-03 |
| 02 | Regression fixture | planned | TBD | TBD | 01 | 2026-05-03 |
| 03 | Prompts, docs, and validation | planned | TBD | TBD | 01, 02 | 2026-05-03 |

## Acceptance

- The alpha-kitchen dogfood validator report shape is covered by a fixture.
- The fixture validates without `malformed_validator_report`.
- Invalid validator reports return specific structured diagnostics.
- `de status --json` exposes a `repair_report_schema` next action for
  report-schema errors.
- Validator prompts and references show canonical statuses and discourage
  `completed`.

## Validation

Spec-only validation:

```bash
rg -n "validator-010|completed|repair_report_schema|missing_validation_evidence|inconsistent_validation_evidence" specs/rfc-0019-validator-report-schema-diagnostics
git diff --check -- specs/rfc-0019-validator-report-schema-diagnostics
```

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

## Activity Log

- 2026-05-03 codex: authored ready-for-implementation RFC for GitHub issue #2
  inside `specs/rfc-0019-validator-report-schema-diagnostics/`.
