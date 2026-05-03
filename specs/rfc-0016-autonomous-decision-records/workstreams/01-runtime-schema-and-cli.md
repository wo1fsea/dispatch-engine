---
spec_id: rfc-0016-autonomous-decision-records
workstream_id: "01"
language: en-US
audience: agent
doc_type: workstream
status: planned
---

# Runtime Schema And CLI

## Scope

Add structured autonomous technical decision metadata to the existing decision
resolution path.

## Files

- `scripts/dispatch_engine/decisions.py`
- `scripts/dispatch_engine/cli.py`
- focused tests under `tests/`

## Requirements

- Extend `resolve_decision` without breaking existing callers.
- Validate the autonomous metadata invariants from `TECH.md`.
- Add Codex-facing CLI flags for autonomous technical resolution.
- Preserve append-only `decisions.jsonl` behavior and normal
  `decision.resolved` event emission.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_autonomous_decision_records
python3 scripts/de.py resolve-decision --help
```
