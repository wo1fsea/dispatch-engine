---
language: en-US
audience: mixed
doc_type: spec
---

# Host Heartbeat Snapshot Producer Product Spec

## Summary

The dashboard can display host heartbeat freshness only if interactive Codex
records heartbeat wakeups into Dispatch Engine run state. Detached runs need a
Codex-facing way to write a run-scoped host heartbeat snapshot after each
heartbeat check and before terminal cleanup.

This spec covers GitHub issue #28.

## Goals / Non-goals

- Goal: Add a Codex-facing command or equivalent workflow to write
  `.dispatch/runs/<run-id>/host-heartbeat.json`.
- Goal: Make every host heartbeat check record `automation_id`, owner,
  interval, last/next wakeup, cursor, status, and terminal stop metadata.
- Goal: Keep `/api/host-heartbeat` read-only.
- Non-goal: Make Dispatch Engine create Codex App automations.
- Non-goal: Let the dashboard resolve decisions or wake the chat.

## Behavior Invariants

1. Host heartbeat automation remains owned by the Codex host layer.
2. Dispatch Engine may provide a CLI write helper for the heartbeat snapshot.
3. Dashboard host heartbeat state comes from the snapshot or terminal
   derivation only; it must not infer freshness from agent heartbeats.
4. When a run is terminal, the heartbeat snapshot records stopped status before
   the host automation is deleted or paused.
5. Missing snapshots on active runs render as missing/unavailable, not as live.

## States And Edge Cases

- Active run with snapshot: dashboard shows last wakeup and next wakeup.
- Active run without snapshot: dashboard shows setup/missing state.
- Terminal run with snapshot: dashboard shows stopped with stop reason.
- Terminal run without snapshot: dashboard may derive stopped from `run.json`.

## Open Questions

- Should the command compute `next_wakeup_at` from interval when not provided,
  or require the host automation to pass it explicitly?
