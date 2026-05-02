---
language: en-US
audience: agent
doc_type: spec
---

# Decision Blocker Protocol Tech Spec

## Proposed Changes

- Add skill/reference guidance for when to request decisions.
- Define decision/blocker JSONL shapes.
- Reuse existing `decision.requested` event.
- Add minimal read/write helpers because current `decisions.jsonl` support only initializes imported plan decisions and does not query or resolve runtime decisions/blockers.

## Implemented Runtime Surface

- `dispatch_engine.decisions.record_decision_request(...)`
- `dispatch_engine.decisions.resolve_decision(...)`
- `dispatch_engine.decisions.list_decisions(...)`
- `dispatch_engine.decisions.list_pending_decisions(...)`
- `dispatch_engine.decisions.record_blocker(...)`
- `dispatch_engine.decisions.resolve_blocker(...)`
- `dispatch_engine.decisions.list_blockers(...)`
- `dispatch_engine.decisions.list_unresolved_blockers(...)`
- `dispatch_engine.decisions.validate_decision_blocker_state(...)`

The helper is intentionally small: it appends JSONL records, folds latest state by id, emits observability events, and exposes unresolved blocker validation. It does not choose resolutions or schedule work.

## Record Locations

```text
.dispatch/runs/<run-id>/decisions.jsonl
.dispatch/runs/<run-id>/blockers.jsonl
```

Events emitted by the helper:

- `decision.requested`
- `decision.resolved`
- `blocker.recorded`
- `blocker.resolved`

## Workstreams

1. `01-decision-guidance`: skill/reference/prompt guidance.
2. `02-decision-state`: durable decision/blocker state helpers if needed.
3. `03-status-docs-validation`: status/docs validation.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg "decision.requested|blocked|pending decision|resolve|blocker.recorded" references specs/rfc-0011-decision-blocker-protocol
git diff --check
```
