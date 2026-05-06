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
  - references/review-validator-protocol.md
  - references/prompts/validator-protocol.md
  - references/prompts/reviewer-validator-protocol.md
  - references/prompts/coordinator-protocol.md
  - scripts/dispatch_engine/agents.py
  - scripts/dispatch_engine/state.py
  - scripts/dispatch_engine/dashboard.py
  - tests/test_review_validator_protocol.py
  - tests/test_status_tail.py
  - tests/test_dashboard_observer.py
  - specs/rfc-0032-validator-artifact-evidence-gate/
depends_on: []
updated: 2026-05-06
---

# Workstream 01: Validator Artifact Evidence Gate

Make missing validator artifacts a visible acceptance-gating condition and add
regression coverage for passed validators with malformed evidence.

Validation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
git diff --check
```
