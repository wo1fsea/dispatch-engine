---
id: 03-inspect-plan
language: en-US
audience: agent
doc_type: spec
status: ready
owner: unassigned
branch:
pr:
files:
  - scripts/dispatch_engine/inspect.py
  - scripts/dispatch_engine/planner.py
depends_on:
  - 01-runtime-state
claimed_at:
lease_expires_at:
updated: 2026-05-02
---

# Inspect And Plan Workstream

## Scope

Reduce inspection noise and make planning conservative about broad or risky objectives.

## Plan

1. Deduplicate and prioritize planning-source output.
2. Keep human inspect output bounded.
3. Preserve machine-readable fields for JSON output.
4. Add conservative pending-decision heuristic for broad, risky, or multi-domain objectives.
5. Keep one workstream as the default plan.

## Progress

Not started.

## Validation

- `python scripts/de.py inspect .`
- `python scripts/de.py inspect . --json`
- `python scripts/de.py plan . --objective "update backend API and UI flow"`
- Confirm broad objective records a pending decision.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
