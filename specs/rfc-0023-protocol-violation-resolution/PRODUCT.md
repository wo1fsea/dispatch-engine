---
language: en-US
audience: mixed
doc_type: spec
---

# Protocol Violation Resolution Product Spec

## Summary

Dispatch Engine should let interactive Codex or a coordinator durably record
that a protocol violation has been acknowledged, accepted with concerns, judged
false positive, or superseded by later validation evidence. Original violation
evidence must remain intact, while `status --json`, `alerts --json`, and
`next_actions` should distinguish unresolved protocol blockers from reviewed
ones.

This spec covers GitHub issue #19.

## Goals / Non-goals

- Goal: Add a durable `.dispatch/` record for protocol-violation resolutions.
- Goal: Expose a Codex-facing CLI command for recording a resolution with
  actor, rationale, evidence, and matching scope.
- Goal: Make status and alerts report resolved versus unresolved protocol
  violations without deleting historical events or worker reports.
- Goal: Stop unresolved-action hints from counting violations that were
  explicitly resolved or superseded.
- Goal: Normalize historical `protocol.violation` events whose payload uses
  `kind` instead of `violation`.
- Non-goal: Automatically mark a blocked run completed after a resolution.
- Non-goal: Restart or re-enter a completed coordinator.
- Non-goal: Weaken capability enforcement or treat unresolved overreach as
  valid by default.

## Behavior Invariants

1. Resolution records are append-only and live under the run's `.dispatch/`
   state.
2. A resolution includes at least actor, resolution kind, rationale, evidence,
   timestamp, and a selector for the violation it addresses.
3. Resolution kinds are explicit and machine-readable:
   `acknowledged`, `accepted_with_concerns`, `superseded_by_validation`, and
   `false_positive`.
4. Status keeps original detected/event-carried protocol violations visible,
   while also reporting `resolved_count`, `unresolved_count`, and the matching
   resolution records.
5. Alerts distinguish unresolved protocol violations from resolved ones. A
   resolved violation should not keep `repair_protocol_violations` in
   `next_actions`.
6. Resolution matching is conservative. If a selector is too broad or cannot
   match a current violation, the command should fail instead of silently
   creating a misleading resolution.
7. Terminal runs remain terminal. Resolution records can improve audit status
   for cancelled or failed runs, but they do not rewrite terminal outcomes.

## States And Edge Cases

- Active blocked run with one violation resolved: unresolved count decreases
  and `repair_protocol_violations` count reflects only the remaining blockers.
- Active blocked run with all violations resolved: no generic protocol-repair
  next action remains, though other blockers may still appear.
- Cancelled run with later resolution records: cancellation remains visible;
  status exposes the resolution audit trail.
- Historical event payload has `kind: capability_overreach` but no
  `violation`: status and alerts normalize it to `capability_overreach`.
- Duplicate resolution attempts for the same selector are allowed only if the
  records are separately visible; latest records must not hide audit history.

## Open Questions

- Should a future coordinator re-entry command turn "all violations resolved"
  into a new repair workstream automatically?
- Should resolutions be editable or superseded through a separate reversal
  command, or remain append-only forever?
