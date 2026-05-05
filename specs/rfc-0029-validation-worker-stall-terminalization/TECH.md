---
language: en-US
audience: agent
doc_type: spec
---

# Validation Worker Stall Terminalization Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #20 came from Dispatch Engine dogfood run `20260505T083305787272Z`.
Worker `worker-04-dashboard-validation` remained running without a terminal
report. Interactive Codex ran validation manually and cancelled the run, after
which status no longer showed the original stalled-worker condition.

Relevant files:

- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/events.py`
- `scripts/dispatch_engine/dashboard.py`
- `references/prompts/coordinator-protocol.md`
- `references/prompts/reviewer-validator-protocol.md` or equivalent validator
  guidance if present
- `tests/test_status_tail.py`
- `tests/test_dashboard_observer.py`
- `tests/test_provider_native_worker_lifecycle.py` if present or added

## Change Gate

- Problem: Missing validation reports can remain invisible until the human asks.
- Smallest new surface: lifecycle diagnostics and validator prompt/report
  guidance. Do not add automatic process killing first.
- Validation: focused lifecycle/status/dashboard tests, full unittest discovery,
  and `git diff --check`.

## Proposed Changes

1. Define stale validation criteria:
   - worker role/profile indicates validation/review, or workstream is a
     validation gate;
   - no terminal report;
   - no fresh heartbeat or process evidence beyond threshold;
   - run not already terminalized with explicit cancellation evidence.
2. Surface stale validation state:
   - `lifecycle_diagnostics` entry with worker id, workstream id, last evidence,
     threshold, and suggested next action;
   - material alert when stale validation blocks acceptance;
   - dashboard validators/alerts views use the same diagnostic.
3. Strengthen validator guidance:
   - validation workers must write a terminal report even when validation fails
     or is blocked;
   - coordinator must not accept validation without report evidence.
4. Preserve cancellation evidence:
   - cancelled runs retain a diagnostic summary of incomplete validation if the
     stale condition existed before cancellation.

## Validation Plan

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg -n "validation worker|stale|lifecycle_diagnostics|terminal report" references scripts tests specs/rfc-0029-validation-worker-stall-terminalization
git diff --check
```

## Risks

- Long validations could be marked stale too aggressively. Use conservative
  thresholds and expose next actions instead of hard failure first.
- Retaining cancelled-run diagnostics could duplicate cancellation alerts.
  Deduplicate by worker id and workstream id.
