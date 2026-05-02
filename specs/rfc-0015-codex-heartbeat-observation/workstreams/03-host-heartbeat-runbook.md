---
language: en-US
audience: agent
doc_type: workstream
status: planned
updated: 2026-05-02
---

# 03 - Host Heartbeat Runbook

## Scope

Document how interactive Codex should create or suggest a thread heartbeat
monitor after starting a detached run in hosts that support wakeups.

The runbook should include:

- when to create a heartbeat
- recommended interval guidance
- heartbeat prompt shape
- material-change reporting rules
- fallback wording when host wakeups are unavailable

## Acceptance

1. Operator docs distinguish DE runtime state from host wakeup mechanics.
2. The heartbeat prompt only describes the task; schedule/thread metadata stays
   in the host automation configuration.
3. The runbook says to report decisions, blockers, failures, completed
   workstreams, and validation evidence, not unchanged activity.
