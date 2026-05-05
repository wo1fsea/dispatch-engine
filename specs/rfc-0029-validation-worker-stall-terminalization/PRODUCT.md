---
language: en-US
audience: mixed
doc_type: spec
---

# Validation Worker Stall Terminalization Product Spec

## Summary

Validation workers must either produce terminal validation evidence or become
visible as stalled/incomplete. A run should not rely on interactive Codex to
manually notice that a validation worker remained running without a report.

This spec covers GitHub issue #20.

## Goals / Non-goals

- Goal: Detect provider-native workers that remain running without heartbeat,
  terminal report, or launch evidence past a conservative threshold.
- Goal: Surface stalled validation/review workers in status, alerts, dashboard,
  and coordinator reports.
- Goal: Give interactive Codex a clear recovery path: wait, cancel, resume, or
  rerun validation.
- Goal: Preserve the coordinator-only implementation boundary.
- Non-goal: Automatically kill all long-running workers; some validations are
  legitimately slow.
- Non-goal: Mark work accepted without validator evidence.

## Behavior Invariants

1. A validation/review worker must provide a terminal report before its
   workstream is accepted.
2. A worker with no recent heartbeat or report is reported as stale/stalled
   rather than silently `running`.
3. Cancelling a run terminalizes worker state and preserves evidence explaining
   why validation did not complete.
4. Status and dashboard distinguish active running workers from stale workers.
5. Coordinator reports must not claim validation passed unless report files or
   accepted evidence exist.

## User Experience

- Interactive Codex can see why a dogfood run is stuck.
- A validation worker that never reports produces a material alert and a next
  action.
- The dashboard validators page becomes meaningful when validation evidence or
  missing evidence exists.

## Open Questions

- What default stale threshold should apply to validation workers versus normal
  implementation workers?
- Should stale validation workers create protocol violations or material alerts
  first?
