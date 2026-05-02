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

Dispatch Engine is skill-first and runtime-when-necessary. Describe workflow
judgment, coordinator behavior, provider-native spawn guidance, review
criteria, validation expectations, and operator procedures in the skill,
references, and prompt templates by default. Move behavior into runtime code
only when it must be durable, queryable, resumable, mechanically validated, or
reported through status/tail.

Coordinator owns spawn decisions; Dispatch Engine owns the durable
observability contract.

## Loop Shape

```text
imported plan -> provider CLI coordinator -> coordinator-spawned agents -> reports -> review/validation guidance -> status/tail
```

1. Plan import creates durable run state from a Codex-prepared plan.
2. `de run <repo> --dry-run` renders the provider CLI coordinator command and coordinator prompt from imported run state without state writes.
3. `de run <repo>` launches the provider CLI coordinator in the foreground, registers it in `.dispatch/`, captures logs, and records completion or failure.
4. The provider CLI coordinator plans, dispatches, monitors, summarizes, and requests decisions, but remains coordinator-only.
5. The coordinator may spawn workers, reviewers, or validators through provider-native mechanisms, but registered `.dispatch/` state remains the source of truth.
6. Workers receive one workstream prompt at a time, scoped by the imported plan and current run state.
7. Spawned agent prompt snapshots, reports, logs, status records, and heartbeats are stored as run-scoped runtime content under `.dispatch/runs/<run-id>/prompts/`, `reports/`, `reviews/`, `validation/`, `logs/`, `agents/`, and `heartbeats/`.
8. Review and validation guidance lives in skill/reference prompts first; runtime report readers and violation checks are added only where durable evidence is needed.
9. Validators execute or record the commands declared in the plan when validation evidence is required.
10. Status and tail readers expose run progress from durable files and events.

## Provider Coordinator Launch

The current launch surface supports both live foreground execution and dry-run
rendering:

```bash
python3 scripts/de.py run <repo>
python3 scripts/de.py run <repo> --provider codex
python3 scripts/de.py run <repo> --provider claude
python3 scripts/de.py run <repo> --dry-run
python3 scripts/de.py run <repo> --provider codex --dry-run
python3 scripts/de.py run <repo> --provider claude --dry-run
```

If `--provider` is omitted, Dispatch Engine uses provider `codex`. Provider
`codex` uses a `codex exec` command shape. Provider `claude` uses a `claude -p`
command shape. Dry-run renders the selected command, run id, state directory,
and coordinator prompt marker or preview; it does not launch a provider process
or write runtime state.

Live launch writes `prompts/coordinator-001.md`,
`logs/coordinator-001.stdout.log`, and
`logs/coordinator-001.stderr.log` under `.dispatch/runs/<run-id>/`; registers
`coordinator-001`; emits `coordinator.started`; and then records
`coordinator.completed` or `coordinator.failed` when the provider process exits.
Both Codex and Claude receive a short launch instruction pointing to the
recorded prompt snapshot instead of receiving the full coordinator prompt inline.

The provider CLI process is a coordinator. It may write Dispatch Engine runtime
state under `.dispatch/`, register implementation agents, emit lifecycle
events, and request decisions. It must not directly edit project files to
satisfy the objective.

## Coordination Rules

- A workstream is ready only when all `depends_on` entries are accepted or explicitly skipped by a recorded decision.
- A workstream is accepted only after coordinator/operator judgment combines
  worker, reviewer, validator, and decision/blocker evidence. Runtime status may
  display this state, but it must not automate the judgment.
- Parallel workstreams may run together only when their declared write scopes do not overlap, or when the imported plan marks the overlap as coordinated.
- Workstreams with unresolved decisions stay blocked until interactive Codex or the user records a decision.
- The coordinator may retry, pause, or request review, but it must not broaden file scope or invent validation commands without a recorded decision.

## Adapter Neutrality

The runtime loop should express worker, reviewer, and validation evidence as adapter-neutral state. Provider-specific launch details belong in coordinator guidance or adapters; the run state and event protocol should remain stable across providers.

Workers, reviewers, and validators must be registered under
`.dispatch/runs/<run-id>/agents/` before their output is treated as valid. The
coordinator may not substitute its own project-file edits for registered
implementation-agent work.

The rfc-0007 worker adapter baseline is helper-first: it defines registration,
central worker prompt rendering, durable reports, status visibility, and
conservative protocol violations. It does not add a scheduler or launch real
worker provider processes yet.

The rfc-0008 coordinator-spawn contract keeps spawn decisions with the provider
coordinator while requiring every spawned agent to register and report through
the shared `.dispatch/` contract.

Required spawned agent events include `agent.spawned`,
`workstream.assigned`, `agent.heartbeat`, `agent.completed`, `agent.failed`,
and `protocol.violation`.

## Runtime Storage

All Dispatch Engine runtime-generated non-project loop content stays under
`.dispatch/`, including agent registry records, prompt snapshots, reports,
logs, heartbeats, adapter reports, review records, validation output, event
logs, and temporary orchestration files. Accepted source, test, docs, specs, or
configuration changes remain in normal project paths.
