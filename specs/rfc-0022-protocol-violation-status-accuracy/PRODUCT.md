---
language: en-US
audience: mixed
doc_type: spec
---

# Protocol Violation Status Accuracy Product Spec

## Summary

Dispatch Engine should report protocol violations with names that match the
actual problem. Completed workstreams with assigned agents should not be called
unregistered merely because the assigned agent is cancelled, has invalid
evidence, or has stale per-workstream state. Legacy `protocol.violation` events
should not degrade into `unknown` alerts when their payload contains enough
structured capability information.

This spec covers the still-current portion of GitHub issue #16.

## Goals / Non-goals

- Goal: Stop reporting `unregistered_implementation_completion` when a
  workstream has an `assigned_agent` that exists.
- Goal: Report targeted diagnostics for completed workstreams whose assigned
  agent is missing, non-terminal, cancelled/failed, or has invalid evidence.
- Goal: Normalize legacy capability-shaped `protocol.violation` event payloads
  into useful alert types instead of `unknown`.
- Goal: Document the distinction between detected violations and historical
  protocol violation events.
- Non-goal: Make cancelled workers count as valid implementation evidence.
- Non-goal: Rewrite historical `.dispatch` run files.
- Non-goal: Suppress genuine capability overreach.

## Behavior Invariants

1. A completed/implemented/accepted workstream with no assigned or matching
   implementation agent may still report `unregistered_implementation_completion`.
2. A completed workstream with an assigned agent record that is cancelled or
   failed reports a targeted invalid-assigned-agent violation.
3. A completed workstream with an assigned agent record whose report is invalid
   reports the report/scope/capability violation, not an unregistered-agent
   fallback.
4. `protocol.violation` events without a `violation` string but with capability
   fields are normalized as capability overreach or compatibility event
   diagnostics.
5. `de alerts --json` remains useful for old dogfood events and does not show
   `violation: "unknown"` when the payload has a clear shape.
6. Aggregate `run.json` workstream state and `workstreams/*.json` state should
   not produce contradictory misleading diagnostics without enough details to
   inspect the mismatch.

## States And Edge Cases

- `assigned_agent` exists and completed with valid report: no completion
  violation.
- `assigned_agent` exists but agent is cancelled: targeted invalid assigned
  agent violation.
- `assigned_agent` exists but report is missing or malformed: report violation
  remains the primary signal.
- Historical event payload has `capability` but no `violation`: alert should
  explain capability overreach compatibility, not `unknown`.
- Historical run aggregate says planned while per-workstream file says
  completed: status should surface enough context to inspect the per-workstream
  source.

## Open Questions

- Should stale aggregate/per-workstream mismatch become a lifecycle diagnostic
  in this spec or remain a future consistency check?
