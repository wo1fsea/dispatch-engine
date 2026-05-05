---
language: en-US
audience: mixed
doc_type: spec
---

# Safe Parallel Dispatch Contract Product Spec

## Summary

Dispatch Engine should make safe parallel worker dispatch the default
coordinator behavior when the imported plan contains independent, non-conflicting
workstreams. Interactive Codex and the coordinator should explicitly analyze
dependencies, write scopes, review gates, and capability blockers before
dispatch. Work should be serialized only when there is a real dependency,
shared-write conflict, decision blocker, review gate, provider limit, or other
recorded rationale.

This spec covers GitHub issue #22.

## Goals / Non-goals

- Goal: Make plan authoring include an explicit parallelism analysis, including
  safe batches, serial gates, write-scope conflicts, and a concurrency budget.
- Goal: Make coordinator prompts require a ready-workstream pass before each
  dispatch cycle and batch-spawn all currently safe ready workers within the
  concurrency budget.
- Goal: Require an auditable serial rationale whenever an apparently ready
  workstream is not spawned.
- Goal: Surface under-parallelization signals in coordinator reports and, where
  mechanically useful, status or plan diagnostics.
- Goal: Preserve coordinator ownership of provider-native spawning and
  Dispatch Engine ownership of durable observability.
- Non-goal: Add a deterministic runtime scheduler that replaces coordinator
  judgment.
- Non-goal: Force parallel work when write scopes overlap unsafely, validation
  depends on prior work, provider limits are unknown, or the user requested a
  serial review loop.
- Non-goal: Let workers broaden write scope or share files without explicit
  coordination.

## Behavior Invariants

1. The default planning posture is parallel-first: identify independent,
   non-overlapping workstreams before accepting a serial chain.
2. Plans may still choose serial execution, but each serial edge should have a
   concrete rationale such as dependency, shared file, shared API contract,
   visual review gate, validation gate, or provider concurrency limit.
3. A coordinator dispatch cycle starts by computing currently ready
   workstreams: all dependencies accepted, no unresolved blockers, capability
   warnings handled, and no unsafe write conflict with already-running work.
4. The coordinator should spawn every safe ready workstream up to the declared
   concurrency budget.
5. Workstreams with shared files can run in parallel only when the plan marks
   the overlap as coordinated and states the integration protocol.
6. The coordinator report must include dispatch batches, active concurrency,
   serialized-ready workstreams, and the rationale for every intentional serial
   decision.
7. Status and alerts should remain honest: if a run has only one worker active
   because all other work is blocked, it should say blocked/serialized rather
   than imply provider capacity was unavailable.
8. The runtime may provide read-only diagnostics or validation helpers, but it
   must not silently rewrite the imported plan into a different schedule.

## States And Edge Cases

- All workstreams disjoint: coordinator spawns the first ready batch in
  parallel up to the concurrency budget.
- Disjoint workstreams with a final integration gate: independent workers run
  together; integration/review/validation waits for their reports.
- Shared file without coordination: plan import or diagnostics should force a
  dependency, a smaller file split, or an explicit coordinated-overlap record.
- Broad shared root such as `dashboard/`: the planner should split by concrete
  files where possible or justify a serial/integrator gate.
- A ready workstream is not spawned because provider-native spawn is unavailable
  or the host limit is reached: coordinator records the provider/host rationale.
- User requests strict serial review: plan records the user review gate and
  coordinator does not flag it as accidental under-parallelization.
- Existing plans without parallel metadata: coordinator falls back to
  `depends_on` and file-scope checks, then records that parallelism metadata was
  absent.

## Open Questions

- Should the first runtime helper be a warning-only `de plan-diagnostics`
  command or part of `de init` output?
- What default coordinator concurrency budget should be recommended for Codex
  and Claude providers?
- Should status expose `ready_but_serialized` as a first-class summary, or keep
  it in coordinator reports until dogfood shows the right shape?
