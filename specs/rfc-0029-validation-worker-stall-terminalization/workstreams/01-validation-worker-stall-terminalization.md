---
id: 01-validation-worker-stall-terminalization
spec: rfc-0029-validation-worker-stall-terminalization
status: ready
depends_on: []
---

# 01 Validation Worker Stall Terminalization

Detect validation/review workers that remain running without fresh heartbeat or
terminal report, and surface the condition before acceptance.

Acceptance:

- Status exposes stale validation diagnostics and next actions.
- Dashboard validators/alerts can show missing terminal validation evidence.
- Cancelling a run preserves incomplete validation evidence.
