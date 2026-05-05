---
id: 01-status-plan-consistency
spec: rfc-0026-dashboard-status-plan-consistency
status: ready
depends_on: []
---

# 01 Status Plan Consistency

Normalize workstream state across `de status --json`, `/api/status`, and
`/api/plan`.

Acceptance:

- Assigned workstream files do not appear as planned/unassigned in status.
- Dashboard status and plan APIs agree on counts and assignments.
- Regression tests cover the issue #24 dogfood shape.
