---
language: en-US
audience: agent
doc_type: spec
---

# Dashboard Status Plan Consistency Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #24 was reported from alpha-kitchen run `20260505T173944412241Z`.
Observed state after cancellation:

- `python3 scripts/de.py status ... --json` returned
  `workstream_counts: {"planned": 6}`,
  `workstream_progress.unassigned: 6`, and no assignments.
- The durable workstream file for
  `01-runtime-contract-live-source-mode` still recorded an assigned worker.
- `/api/plan` showed the assigned/running workstream while `/api/status` did
  not.

Relevant files:

- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/dashboard.py`
- `scripts/dispatch_engine/events.py`
- `tests/test_status_tail.py`
- `tests/test_dashboard_observer.py`
- dashboard static assets if UI label normalization is needed

## Change Gate

- Problem: Codex and dashboard users receive contradictory run progress.
- Smallest new surface: shared normalization helpers and regression fixtures.
- What will be deleted or replaced: duplicate status-only workstream counting
  that ignores durable workstream files.
- Validation: focused status/dashboard tests, full unittest discovery, and
  `git diff --check`.

## Proposed Changes

1. Locate every status/dashboard code path that counts workstreams.
2. Introduce or reuse a single normalization path for workstream state.
3. Prefer explicit workstream file state over imported-plan defaults when a
   workstream file exists.
4. Merge assignment evidence from durable workstream files and assignment
   events into `workstream_assignments`.
5. Preserve historical assignment evidence for terminal runs.
6. Add a regression fixture that reproduces the issue #24 mismatch.
7. Update dashboard API tests so `/api/status` and `/api/plan` agree on counts
   and assigned workstreams.

## Validation Plan

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

Dogfood validation should include:

```bash
python3 scripts/de.py status <fixture-repo> --run-id <run-id> --json
python3 scripts/de.py dashboard <fixture-repo> --run-id <run-id> --once --json
```

## Risks

- A naive fix could double-count workstreams that appear in both plan and file
  form. Tests must cover deduplication by workstream id.
- A terminal-run fix could make cancelled work look active. UI should separate
  current run terminal state from historical assignment evidence.
