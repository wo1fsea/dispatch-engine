---
language: en-US
audience: agent
doc_type: workstream
status: planned
updated: 2026-05-02
---

# 02 - Codex-Facing Control Surface

## Scope

Add or refine machine-readable runtime commands that interactive Codex can call
after a heartbeat wakeup or user status request:

- `status --json` `next_actions`
- event delta reads
- alert reads
- decision resolution after user approval
- report-schema repair or compatibility actions if dogfood proves necessary

## Acceptance

1. Commands are non-interactive and JSON-first.
2. Status includes actionable next steps for Codex.
3. Decision resolution records the user's approved option in `.dispatch/`.
4. Tests cover pending decisions, protocol violations, and unchanged status.
