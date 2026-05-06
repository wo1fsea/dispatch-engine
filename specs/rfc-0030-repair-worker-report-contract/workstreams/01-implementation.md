---
workstream_id: 01-implementation
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - references/prompts/worker-protocol.md
  - references/prompts/coordinator-protocol.md
  - scripts/dispatch_engine/agents.py
  - scripts/dispatch_engine/state.py
  - tests/test_worker_adapter_protocol.py
  - tests/test_status_tail.py
  - specs/rfc-0030-repair-worker-report-contract/
depends_on: []
updated: 2026-05-06
---

# Workstream 01: Repair Worker Report Contract

Implement the narrow issue #25 contract: repair workers must produce canonical
worker reports and tests must prove that repair evidence does not create a
second malformed-report violation.

Validation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
git diff --check
```
