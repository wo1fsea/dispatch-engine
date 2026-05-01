---
language: en-US
audience: mixed
doc_type: spec
---

# Explicit Plan Orchestrator Boundary Product Spec

## Summary

Correct Dispatch Engine's product boundary. Interactive Codex and the installed skill own repository understanding, user interaction, planning judgment, workstream splitting, and validation strategy. Dispatch Engine runtime owns durable execution state, event logs, status reporting, and later the mechanical orchestration loop.

The runtime must not pretend to discover a target repository's rules or infer the right plan from heuristics. It should accept an explicit dispatch plan prepared by Codex from the target repository's own conventions, then persist and execute that plan.

## Goals / Non-goals

- Goal: Make `.dispatch/` the only place Dispatch Engine writes non-project runtime content in a target repository.
- Goal: Replace runtime-owned `inspect` and heuristic `plan` with Codex-owned discovery plus an explicit dispatch plan contract.
- Goal: Add a plan initialization path that imports a prepared dispatch plan into durable run state.
- Goal: Keep project content changes in the target repository's normal locations rather than under `.dispatch/`.
- Goal: Preserve useful durable run state, status, tail, event, decision, workstream, and artifact concepts from the existing runtime.
- Goal: Prepare the boundary for a future runtime loop with a main orchestrator agent, worker agents, and reviewer agents.
- Non-goal: Implement real worker execution in this spec.
- Non-goal: Define one universal spec format for every target repository.
- Non-goal: Ask the runtime to infer repository standards, choose validation commands, or split work without an explicit plan.
- Non-goal: Add a daemon, dashboard, database, or remote service.

## Behavior Invariants

1. Interactive Codex reads the target repository's local instructions, code patterns, docs, tests, and user conversation before producing a dispatch plan.
2. Dispatch Engine runtime does not scan the target repository to infer planning rules, repo conventions, validation commands, or workstream splits.
3. Any Dispatch Engine-generated non-project file in a target repository is written under `.dispatch/`.
4. Project files changed to satisfy the user's objective remain in their normal repository paths, not under `.dispatch/`.
5. A generated dispatch plan is stored under `.dispatch/plans/` when Dispatch Engine or the skill writes it into the target repository.
6. The runtime imports an explicit dispatch plan into `.dispatch/runs/<run-id>/` and records the import through events.
7. `de status` and `de tail` continue to read durable run state without relying on chat memory.
8. The runtime rejects or clearly reports malformed plans instead of filling gaps with invented repository knowledge.
9. Parallelism decisions come from the explicit dispatch plan, including dependencies and overlapping write scopes.
10. Pending decisions are explicit plan entries or runtime execution blockers, not heuristic guesses from objective text.
11. Future worker and reviewer prompts are generated from the imported plan and runtime state, not from a fresh runtime inspection pass.
12. Installing or copying the skill includes the bundled runtime, protocol references, and schema/reference docs needed to operate the explicit-plan flow.

## States and Edge Cases

- No `.dispatch/` directory exists in the target repository.
- `.dispatch/plans/` exists but contains no plan files.
- A plan path outside `.dispatch/` is supplied by the operator.
- A generated plan would otherwise be written outside `.dispatch/`.
- A plan has no workstreams.
- A plan has duplicate workstream ids.
- A plan has dependencies on missing workstreams.
- Two parallel workstreams declare overlapping write scopes.
- A plan references validation commands but the target repository lacks the toolchain.
- A previously imported run exists and a new plan is imported.
- The old `inspect` or `plan` CLI command is invoked after deprecation/removal.

## Open Questions

- Should `de init --plan <path>` copy externally supplied plan files into `.dispatch/plans/`, or only record the source path in run metadata?
- Should plan schema validation be implemented as in-code checks first, or should a JSON Schema file be added under `references/`?
- Should future orchestrator execution start as `de run --run-id <id>`, or should `de init --plan` optionally start the run loop?
