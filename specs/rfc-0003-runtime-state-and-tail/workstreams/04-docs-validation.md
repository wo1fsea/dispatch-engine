---
id: 04-docs-validation
language: en-US
audience: agent
doc_type: spec
status: ready
owner: unassigned
branch:
pr:
files:
  - references/event-protocol.md
  - README.md
  - specs/rfc-0003-runtime-state-and-tail/**
depends_on:
  - 01-runtime-state
  - 02-status-tail
  - 03-inspect-plan
claimed_at:
lease_expires_at:
updated: 2026-05-02
---

# Documentation And Validation Workstream

## Scope

Document the expanded event protocol and record validation evidence for the runtime-state and tail work.

## Plan

1. Update `references/event-protocol.md`.
2. Update README examples only if CLI usage changes materially.
3. Record validation evidence in this workstream and `STATUS.md`.
4. Confirm no `.dispatch/` state is staged.

## Progress

Not started.

## Validation

- Full command list in `TECH.md`.
- `git status --short` shows no generated `.dispatch/` files.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
