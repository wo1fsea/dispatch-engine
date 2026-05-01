---
language: en-US
audience: agent
doc_type: design
---

# Orchestrator Loop

Use this reference when designing the future Dispatch Engine runtime loop.

## Boundary

The loop starts from imported explicit plan state under `.dispatch/runs/<run-id>/`. It does not scan the repository to infer conventions, split work, choose validation commands, or invent pending decisions.

Interactive Codex remains the user-facing reasoning layer. It can keep talking with the user, resolve decisions, review summaries, and poll runtime `status` and `tail` output while the runtime handles mechanical scheduling.

## Loop Shape

```text
imported plan -> scheduler -> workers -> reviewer -> validation -> status/tail
```

1. Plan import creates durable run state from a Codex-prepared plan.
2. The scheduler selects ready workstreams from imported dependencies, `parallel_group`, declared write scopes, and decision blockers.
3. Worker adapters receive one workstream prompt at a time, scoped by the imported plan and current run state.
4. Worker reports are stored as run-scoped runtime content under `.dispatch/runs/<run-id>/`.
5. Reviewer adapters evaluate worker output before the scheduler marks the workstream accepted.
6. Validation runners execute or record the commands declared in the plan.
7. Status and tail readers expose run progress from durable files and events.

## Scheduling Rules

- A workstream is ready only when all `depends_on` entries are accepted or explicitly skipped by a recorded decision.
- Parallel workstreams may run together only when their declared write scopes do not overlap, or when the imported plan marks the overlap as coordinated.
- Workstreams with unresolved decisions stay blocked until interactive Codex or the user records a decision.
- The scheduler may retry, pause, or request review, but it must not broaden file scope or invent validation commands.

## Adapter Neutrality

The runtime loop should express worker, reviewer, and validation steps as adapter-neutral jobs. Provider-specific launch details belong in adapters; the run state and event protocol should remain stable across providers.

## Runtime Storage

All generated non-project loop content stays under `.dispatch/`, including worker prompt snapshots, adapter reports, review records, validation output, event logs, and temporary orchestration files. Accepted source, test, docs, specs, or configuration changes remain in normal project paths.
