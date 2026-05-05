---
language: en-US
audience: agent
doc_type: spec
---

# Dashboard Observer Lifecycle Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #23 came from alpha-kitchen runs:

- Old run: `20260505T162914702948Z`
- Continuation run: `20260505T173944412241Z`

The old dashboard process stayed visible after the old run was cancelled and a
new continuation run started. The browser could remain on the stale dashboard,
making interactive Codex and the human operator inspect the wrong run.

Relevant files:

- `SKILL.md`
- `README.md`
- `references/operator-flow.md`
- `references/operator-guide.md`
- `references/heartbeat-observation.md`
- `scripts/dispatch_engine/dashboard.py` if minimal observer metadata/status
  changes are necessary
- `tests/test_dashboard_observer.py` if runtime metadata changes are added

## Change Gate

- Problem: Dashboard lifecycle is under-specified and can mislead users during
  cancelled or superseded dogfood runs.
- Smallest new surface: skill/operator lifecycle contract plus stale/terminal
  observer metadata if needed.
- Validation: docs grep, focused dashboard tests if runtime changes are made,
  full unittest discovery, and `git diff --check`.

## Proposed Changes

1. Update skill guidance:
   - `de run --detach` requires both host heartbeat and dashboard observer.
   - Dashboard is read-only and never substitutes for heartbeat.
   - Terminal run state requires heartbeat shutdown and dashboard terminal
     state reporting.
2. Define current-run selection:
   - For continuation runs, the current dashboard is the newest active run id.
   - Old run observers should be reported as terminal or superseded.
3. Update operator docs:
   - How to inspect dashboard metadata under `.dispatch/`.
   - How to restart or switch dashboards.
   - How to recognize stale dashboards.
4. Add minimal runtime support only if docs cannot make current state visible:
   - `de dashboard --json` includes run id, terminal state, and stale marker.
   - Dashboard API includes an `observer_state` field for terminal/stale display.

## Validation Plan

Docs-only:

```bash
rg -n "dashboard.*heartbeat|superseded|stale|terminal|observer" SKILL.md README.md references specs/rfc-0027-dashboard-observer-lifecycle
git diff --check
```

If runtime metadata changes:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

## Risks

- Over-eager process cleanup could stop a dashboard the user intentionally kept
  for historical inspection. Prefer stale labeling before automatic killing.
- Making dashboard status sound like heartbeat status would recreate the same
  confusion. Keep the two explicitly separate.
