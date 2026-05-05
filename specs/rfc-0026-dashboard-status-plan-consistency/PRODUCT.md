---
language: en-US
audience: mixed
doc_type: spec
---

# Dashboard Status Plan Consistency Product Spec

## Summary

The dashboard and JSON control surfaces must report the same workstream state
for a run. When `/api/plan` shows assigned or running workstreams, `/api/status`
must not collapse those same workstreams to `planned` or `unassigned`.

This spec covers GitHub issue #24.

## Goals / Non-goals

- Goal: Make `de status --json`, `/api/status`, and `/api/plan` derive
  workstream assignment and progress from the same durable source of truth.
- Goal: Preserve cancelled, completed, and failed terminal run state without
  erasing the last known workstream assignment evidence.
- Goal: Add regression coverage for the alpha-kitchen dogfood shape where a
  workstream file records `assigned` while status reports all workstreams as
  planned/unassigned.
- Goal: Make dashboard overview cards, plan rows, and API summaries agree.
- Non-goal: Add a new scheduler or mutate imported plans.
- Non-goal: Infer success for a workstream that lacks accepted worker/reviewer
  evidence.

## Behavior Invariants

1. A workstream file with `status: assigned` or `state: assigned` is counted as
   assigned/running-compatible, not planned/unassigned.
2. Active assignments recorded in run state, workstream files, or assignment
   events produce the same `workstream_assignments` in status and dashboard
   APIs.
3. Terminal run cancellation may stop agents, but it must not rewrite historical
   workstream files into planned state unless an explicit cancellation event or
   workstream terminal state says so.
4. The dashboard overview, plan explorer, and status JSON must use compatible
   normalization names for planned, assigned/running, blocked, completed,
   failed, and cancelled workstreams.
5. If two durable sources conflict, status should surface a diagnostic or alert
   rather than silently choosing the least informative state.

## User Experience

- Interactive Codex can trust status JSON when reporting progress.
- The dashboard overview progress bar and workstream list stay consistent with
  the plan explorer.
- A stale or cancelled run still shows what was actually assigned before the
  terminal transition.

## Open Questions

- Should conflict diagnostics be warning-only alerts or first-class protocol
  violations?
- Should cancelled assigned workstreams be shown as `cancelled` or
  `assigned_at_cancel` in future dashboard UI?
