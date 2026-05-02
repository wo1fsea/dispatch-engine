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
imported plan -> provider CLI coordinator -> scheduler -> workers -> reviewer -> validation -> status/tail
```

1. Plan import creates durable run state from a Codex-prepared plan.
2. `de run <repo> --dry-run` renders the provider CLI coordinator command and coordinator prompt from imported run state.
3. The provider CLI coordinator plans, dispatches, monitors, summarizes, and requests decisions, but remains coordinator-only.
4. The scheduler selects ready workstreams from imported dependencies, `parallel_group`, declared write scopes, and decision blockers.
5. Worker adapters receive one workstream prompt at a time, scoped by the imported plan and current run state.
6. Worker reports are stored as run-scoped runtime content under `.dispatch/runs/<run-id>/`.
7. Reviewer adapters evaluate worker output before the scheduler marks the workstream accepted.
8. Validation runners execute or record the commands declared in the plan.
9. Status and tail readers expose run progress from durable files and events.

## Provider Coordinator Launch

The current launch surface is dry-run rendering:

```bash
python3 scripts/de.py run <repo> --dry-run
python3 scripts/de.py run <repo> --provider codex --dry-run
python3 scripts/de.py run <repo> --provider claude --dry-run
```

If `--provider` is omitted, Dispatch Engine uses provider `codex`. Provider
`codex` renders a `codex exec` command shape. Provider `claude` renders a
`claude -p` command shape. Dry-run renders the selected command, run id, state
directory, and coordinator prompt marker or preview; it does not launch a
provider process and does not implement project-file changes.

The provider CLI process is a coordinator. It may write Dispatch Engine runtime
state under `.dispatch/`, register implementation agents, emit lifecycle
events, and request decisions. It must not directly edit project files to
satisfy the objective.

## Scheduling Rules

- A workstream is ready only when all `depends_on` entries are accepted or explicitly skipped by a recorded decision.
- Parallel workstreams may run together only when their declared write scopes do not overlap, or when the imported plan marks the overlap as coordinated.
- Workstreams with unresolved decisions stay blocked until interactive Codex or the user records a decision.
- The scheduler may retry, pause, or request review, but it must not broaden file scope or invent validation commands.

## Adapter Neutrality

The runtime loop should express worker, reviewer, and validation steps as adapter-neutral jobs. Provider-specific launch details belong in adapters; the run state and event protocol should remain stable across providers.

Workers, reviewers, and validators must be registered under
`.dispatch/runs/<run-id>/agents/` before their output is treated as valid. The
coordinator may not substitute its own project-file edits for registered
implementation-agent work.

## Runtime Storage

All generated non-project loop content stays under `.dispatch/`, including
agent registry records, reports, logs, heartbeats, worker prompt snapshots,
adapter reports, review records, validation output, event logs, and temporary
orchestration files. Accepted source, test, docs, specs, or configuration
changes remain in normal project paths.
