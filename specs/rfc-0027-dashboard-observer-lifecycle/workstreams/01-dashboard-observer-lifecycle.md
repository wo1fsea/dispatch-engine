---
id: 01-dashboard-observer-lifecycle
spec: rfc-0027-dashboard-observer-lifecycle
status: ready
depends_on: []
---

# 01 Dashboard Observer Lifecycle

Define how interactive Codex launches, reports, retires, and distinguishes
dashboard observers for active, terminal, cancelled, and superseded runs.

Acceptance:

- Skill/operator docs require heartbeat plus dashboard after detached run start.
- Terminal and superseded dashboards are not presented as live progress.
- Runtime metadata is added only if needed to make stale state observable.
