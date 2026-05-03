---
spec_id: rfc-0016-autonomous-decision-records
workstream_id: "02"
language: en-US
audience: agent
doc_type: workstream
status: planned
---

# Status Summary And Tests

## Scope

Expose autonomous technical decision records through `status --json` so final
interactive Codex reports can list all autonomous choices.

## Files

- `scripts/dispatch_engine/state.py`
- focused tests under `tests/`

## Requirements

- Add `autonomous_decisions.count`.
- Add compact `autonomous_decisions.records` with decision id, selected option,
  resolved timestamp, rationale, and validation expectations.
- Keep `decisions.jsonl` as the source of truth.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_autonomous_decision_records
python3 scripts/de.py status --help
```
