---
language: en-US
audience: mixed
doc_type: spec
---

# Validator Artifact Evidence Gate Product Spec

## Summary

A validator cannot be treated as cleanly passed when its report lacks required
artifact evidence. Missing validator artifacts should block acceptance through
visible status/alert/next-action surfaces until repaired, skipped with a valid
reason, or resolved as an accepted protocol concern.

This spec covers GitHub issue #27.

## Goals / Non-goals

- Goal: Require non-skipped validator reports to include non-empty
  `artifacts`.
- Goal: Prevent coordinator summaries from presenting malformed validator
  reports as clean pass evidence.
- Goal: Provide repair guidance for missing validator artifacts.
- Non-goal: Require validators for every workstream.
- Non-goal: Require large artifacts; references to command logs or evidence
  paths are enough.

## Behavior Invariants

1. `status: passed`, `failed`, or `blocked` validator reports require
   `command`, `output_summary`, and non-empty `artifacts`.
2. A validator missing artifacts may still be an agent record, but it is not
   accepted as clean validation evidence.
3. `status --json`, `alerts --json`, and dashboard validator detail expose the
   exact missing field and suggested repair action.
4. Coordinator guidance forbids clean workstream acceptance from malformed
   validator evidence.
5. Valid skipped validator reports remain allowed when they include a skip
   reason and do not claim pass evidence.

## States And Edge Cases

- Missing artifacts but otherwise useful evidence: repair or resolve explicitly.
- Artifact path points to a log path: acceptable when it is a string reference.
- Skipped validator: no artifacts required when skip reason is present and
  status is `skipped`.

## Open Questions

- Should missing artifacts be a hard run blocker or a protocol violation with
  next action first? The initial implementation should keep it actionable and
  visible without rewriting old evidence.
