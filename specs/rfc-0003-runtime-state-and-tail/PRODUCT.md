---
language: en-US
audience: mixed
doc_type: spec
---

# Runtime State And Tail Product Spec

## Summary

Make Dispatch Engine's first dogfood loop useful as an operator-facing runtime shell. A user or interactive Codex should be able to plan an objective, inspect the resulting run state, tail the event log, and see enough durable state to resume the next step without relying on chat memory.

## Goals / Non-goals

- Goal: Expand the current dry-run planner into a durable run-state layout under `.dispatch/runs/<run-id>/`.
- Goal: Add `de tail` so operators can inspect run events from the CLI.
- Goal: Improve `de status` so it reports run, workstream, and pending-decision state rather than a one-line summary only.
- Goal: Improve `de inspect` and `de plan` enough to make the next dogfood iteration less noisy and more actionable.
- Goal: Keep the runtime bundled inside the skill directory and smoke-testable through `python scripts/de.py`.
- Non-goal: Launch real worker agents in this change.
- Non-goal: Implement parallel execution.
- Non-goal: Add a daemon, dashboard, database, or external package install.
- Non-goal: Prescribe a target repository's spec format.

## Behavior

1. When an operator runs `python scripts/de.py plan <repo> --objective "<text>"`, Dispatch Engine creates a run directory under `.dispatch/runs/<run-id>/`.
2. The run directory contains `run.json`, `events.jsonl`, `decisions.jsonl`, `workstreams/`, and `artifacts/`.
3. The generated workstream state is stored as its own file under `workstreams/` rather than only embedded in `run.json`.
4. When no decisions are required, `decisions.jsonl` still exists as an empty append-only log.
5. When an operator runs `python scripts/de.py status <repo>`, Dispatch Engine reports the latest run id, objective, run status, workstream counts by status, pending decisions, and state directory path.
6. When an operator runs `python scripts/de.py tail <repo>`, Dispatch Engine prints events from the latest run in chronological order.
7. When an operator passes an explicit run id to `status` or `tail`, Dispatch Engine reads that run instead of the latest run.
8. When no run exists, `status` and `tail` return a clear no-run message and exit successfully.
9. `inspect` avoids duplicate planning-source output and keeps the default output concise enough for an interactive agent to summarize.
10. `plan` defaults to one workstream and records a pending decision instead of inventing a split when the objective appears broad, risky, or ambiguous.

## States and Edge Cases

- No `.dispatch/` directory exists.
- `.dispatch/runs/` exists but has no run directories.
- Latest run exists but is missing `events.jsonl` or `run.json`.
- A run has no decisions.
- A run has pending decisions.
- A run has one planned workstream.
- An explicit run id does not exist.
- `tail` is invoked on an empty event log.

## Open Questions

- Should `tail` support a follow mode in this spec, or should follow mode wait until worker execution exists?
- Should run ids remain timestamp-only for now, or include a slug from the objective?
- Should the state format use JSON only for MVP, or introduce YAML for human editing?
