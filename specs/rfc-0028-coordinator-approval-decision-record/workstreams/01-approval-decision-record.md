---
id: 01-approval-decision-record
spec: rfc-0028-coordinator-approval-decision-record
status: ready
depends_on: []
---

# 01 Approval Decision Record

Require coordinator approval blockers to become durable pending decisions before
the coordinator exits or waits.

Acceptance:

- Coordinator protocol forbids stdout-only approval prompts.
- Status surfaces missing decision records as material diagnostics.
- Tests cover approval-required reports with no `decisions.jsonl` entry.
