---
language: en-US
audience: mixed
doc_type: spec
---

# Repair Worker Report Contract Product Spec

## Summary

Repair workers are still workers. When a coordinator launches a worker to
repair malformed Dispatch Engine evidence, that repair worker must emit a
schema-valid worker report so the repair path cannot create a second protocol
violation.

This spec covers GitHub issue #25.

## Goals / Non-goals

- Goal: Require report-repair workers to write the canonical worker report
  shape, including `changed_files`, `validation`, `questions`, `blockers`, and
  `risks`.
- Goal: Make repair prompts and status diagnostics distinguish malformed input
  being repaired from malformed repair-worker output.
- Goal: Add regression coverage for a `protocol-report-repair` worker that
  completes without leaving `malformed_worker_report`.
- Non-goal: Add a separate repair-report schema unless the canonical worker
  schema cannot represent repair evidence.
- Non-goal: Auto-edit malformed evidence without a durable repair worker or
  accepted protocol resolution.

## Behavior Invariants

1. A repair worker report is validated against the canonical worker report
   contract.
2. Repair-worker reports may have empty `changed_files` when only runtime
   evidence is inspected, but the field must exist and be an array.
3. Repair-worker reports must include `questions`, even when empty.
4. Status and alerts must not report a repair worker as clean if its own report
   is malformed.
5. Coordinator guidance must tell repair workers to produce a valid worker
   report before marking the repair complete.

## States And Edge Cases

- Malformed input report repaired successfully: repair worker completes and
  writes a valid report plus validation evidence.
- Repair worker cannot repair: report status is `blocked` or `failed` with
  questions/blockers rather than malformed JSON.
- Legacy report aliases remain migration inputs; they are not the canonical
  repair-worker output.

## Open Questions

- Should a future `repair` role exist, or is `worker` plus canonical worker
  report enough?
