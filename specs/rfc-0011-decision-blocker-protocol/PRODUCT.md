---
language: en-US
audience: mixed
doc_type: spec
---

# Decision Blocker Protocol Product Spec

## Summary

Coordinators need a durable way to stop when blocked, ask for human/operator input, and resume after a recorded decision. The reasoning and wording of decisions remain skill-first; runtime stores the durable decision/blocker state.

## Goals / Non-goals

- Goal: Define decision request and resolution records.
- Goal: Show pending decisions in `de status` and `de tail`.
- Goal: Define blocked workstream guidance.
- Non-goal: Build a complex approval workflow UI.
- Non-goal: Make runtime decide risky choices.

## Behavior Invariants

1. A coordinator asks instead of guessing when scope, risk, conflict, or validation is unclear.
2. Decision records are durable under `.dispatch/`.
3. Blocked workstreams remain blocked until a decision or report resolves them.
4. Interactive Codex/user remains the decision maker.

## Accepted Behavior

- Skill/reference guidance defines when coordinators, workers, reviewers, and validators stop for a decision or blocker.
- Runtime decision helpers append decision records to `.dispatch/runs/<run-id>/decisions.jsonl`.
- Runtime blocker helpers append blocker records to `.dispatch/runs/<run-id>/blockers.jsonl`.
- Status readers expose pending decision counts and unresolved blocker counts.
- Validation helpers report `blocked` while blockers remain unresolved and `ok` after they are resolved.
