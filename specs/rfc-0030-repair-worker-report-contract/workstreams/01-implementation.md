---
workstream_id: 01-implementation
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-001-repair-report-contract
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
claimed_at: 2026-05-06T12:49:03+08:00
lease_expires_at: 2026-05-06T14:49:03+08:00
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

## Activity Log

- 2026-05-06 worker-001-repair-report-contract: claimed and started TDD
  implementation for the repair worker report contract.
- 2026-05-06 worker-001-repair-report-contract: added red regression coverage
  for repair-worker prompt guidance and status schema repair actions, then
  implemented prompt/runtime changes and validated the assigned commands.
