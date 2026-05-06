---
language: en-US
audience: agent
doc_type: spec
---

# Repair Worker Report Contract Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #25 came from Alpha Kitchen run `20260505T175620476602Z`, where
`report-repair-001` completed a `protocol-report-repair` workstream but its
own report missed `changed_files` and `questions`, causing
`malformed_worker_report`.

Relevant files:

- `references/prompts/worker-protocol.md`
- `references/prompts/coordinator-protocol.md`
- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/state.py`
- `tests/test_worker_adapter_protocol.py`
- `tests/test_status_tail.py`

## Change Gate

- Problem: repair workers can create malformed worker reports.
- Smallest new surface: prompt/report guidance and focused regression tests.
- Runtime change only if current validation cannot express repair-worker
  report failures cleanly.

## Proposed Changes

1. Strengthen repair prompt guidance:
   - explicitly state that report-repair workers must emit canonical worker
     report JSON;
   - list required fields and allow empty arrays where appropriate.
2. Add a regression fixture for `protocol-report-repair`:
   - valid repair worker report produces no `malformed_worker_report`;
   - missing `changed_files` or `questions` on the repair worker itself remains
     a protocol violation with exact fields.
3. Ensure `status --json` next actions do not create repair loops by treating a
   malformed repair worker as a separate actionable defect.

## Validation Plan

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
rg -n "repair worker|protocol-report-repair|changed_files|questions" references scripts tests specs/rfc-0030-repair-worker-report-contract
git diff --check
```

## Risks

- Over-specializing repair behavior could duplicate the worker protocol. Keep
  repair workers canonical unless a later role-specific schema is justified.
