---
spec_id: rfc-0019-validator-report-schema-diagnostics
workstream_id: 03-prompts-docs-validation
language: en-US
audience: agent
doc_type: workstream
status: planned
owner: TBD
created: 2026-05-03
updated: 2026-05-03
depends_on:
  - 01-schema-diagnostics
  - 02-regression-fixture
---

# Prompts Docs Validation

## Scope

Update validator-facing guidance so future validators emit canonical reports
without relying on compatibility behavior, then validate the full change.

## Files

Expected implementation surfaces:

- `references/review-validator-protocol.md`
- `references/prompts/validator-protocol.md`
- `references/workstream-acceptance-guidance.md`
- `README.md`
- `SKILL.md`
- this spec directory

Do not update `specs/README.md` as part of this issue unless a later operator
explicitly expands the write scope.

## Requirements

- Show canonical validator status values: `passed`, `failed`, `blocked`, and
  `skipped`.
- State that validators must not use `completed` as report status.
- Explain that `validation[]`, `scope_check`, `validated_agent_id`, `risks`,
  and `completed_at` are useful optional fields.
- Tell validators that aggregate `command`, `output_summary`, and `artifacts`
  remain required for non-skipped reports.
- Document skipped validation as `status: "skipped"` plus a specific
  `not_run_reason`.
- Mention that status diagnostics will name exact schema repairs.

## Acceptance Criteria

- Validator prompt examples use `status: "passed"` rather than
  `status: "completed"`.
- Reference docs describe optional structured evidence without making it the
  only accepted evidence mode.
- Documentation and prompts align with the runtime compatibility rule.
- Full unit tests and documentation grep checks pass.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
rg -n "passed|failed|blocked|skipped|completed|validation\\[\\]|repair_report_schema" SKILL.md README.md references specs/rfc-0019-validator-report-schema-diagnostics
git diff --check
```
