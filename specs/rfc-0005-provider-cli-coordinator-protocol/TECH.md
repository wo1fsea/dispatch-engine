---
language: en-US
audience: agent
doc_type: spec
---

# Provider CLI Coordinator Protocol Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Current runtime shape after `rfc-0004-explicit-plan-orchestrator-boundary`:

- `scripts/de.py` is the bundled CLI entrypoint.
- `scripts/dispatch_engine/cli.py` exposes `version`, `init`, `status`, and `tail`.
- `scripts/dispatch_engine/plan_schema.py` validates explicit dispatch plans and imports them into `.dispatch/runs/<run-id>/`.
- `scripts/dispatch_engine/runs.py` creates `run.json`, `events.jsonl`, `decisions.jsonl`, `workstreams/`, `artifacts/`, `reviews/`, and `validation/`.
- `scripts/dispatch_engine/state.py` reports run status and tails events from durable files.
- `scripts/dispatch_engine/events.py` appends JSONL events.
- `references/orchestrator-loop.md`, `references/event-protocol.md`, and `references/worker-protocol.md` describe imported-plan scheduling, event logs, and worker/reviewer boundaries.

The missing stage is provider CLI coordinator launch and observable subagent state. Existing run state can import a plan and report planned workstreams, but it cannot yet register agents, report subagent counts, render Codex or Claude coordinator commands, dry-run launch intent, or enforce that the coordinator remains coordinator-only.

## Change Gate

- Problem: The next architecture stage needs real coordinator supervision without collapsing provider CLIs into provider-specific implementation logic.
- Existing path considered: Let interactive Codex manually launch `codex exec` or `claude -p` and paste results back into chat.
- Why existing path is insufficient: Manual launch loses durable coordinator state, subagent counts, heartbeats, events, protocol violations, and resumable status.
- Smallest new surface: Add an agent registry protocol, event vocabulary, status observability, explicit Codex/Claude provider command templates, and `de run --dry-run` coordinator launcher shape before enabling live process supervision.
- What will be deleted or replaced: No runtime code is deleted in this spec. Later implementation may replace ad hoc status fields with structured agent counts.
- Owner: Dispatch Engine maintainers.
- Validation: Unit tests for provider selection defaults, dry-run command rendering, agent state readers/writers, status counts, event emission, protocol violation detection, and documentation checks.
- Temporary or permanent: Permanent protocol boundary; dry-run launcher is an incremental implementation step toward live launch.
- Removal condition: Superseded only by a richer agent registry protocol that preserves coordinator-only behavior, default Codex provider behavior, explicit Claude provider support, and observable implementation agents.

## Proposed Runtime State

Extend run directories to include agent supervision state:

```text
.dispatch/
  runs/
    <run-id>/
      run.json
      events.jsonl
      decisions.jsonl
      workstreams/
        <workstream-id>.json
      agents/
        <agent-id>.json
      reports/
        <agent-id>.json
      logs/
        <agent-id>.jsonl
      heartbeats/
        <agent-id>.jsonl
      artifacts/
      reviews/
      validation/
```

`agents/<agent-id>.json` is the registry record for a coordinator, worker, reviewer, or validator:

```json
{
  "schema_version": 1,
  "agent_id": "coordinator-001",
  "role": "coordinator",
  "provider": "codex",
  "profile": "codex-exec",
  "status": "running",
  "pid": null,
  "run_id": "20260502T000000000000Z",
  "workstream": null,
  "assigned_files": [],
  "allowed_write_roots": [".dispatch/"],
  "started_at": "2026-05-02T00:00:00Z",
  "last_heartbeat_at": "2026-05-02T00:00:00Z",
  "completed_at": null,
  "report_path": ".dispatch/runs/20260502T000000000000Z/reports/coordinator-001.json",
  "log_path": ".dispatch/runs/20260502T000000000000Z/logs/coordinator-001.jsonl"
}
```

Role rules:

- `coordinator`: may write `.dispatch/` state, assign workstreams, record decisions, launch or declare subagents, review summaries, and request user decisions. `allowed_write_roots` is `.dispatch/` only.
- `worker`: may modify project files only within its assigned workstream file scope, unless a recorded decision expands that scope.
- `reviewer`: may inspect project files and write review reports; project-file edits are allowed only when explicitly assigned as implementation work.
- `validator`: may run or record validation and write runtime validation reports; project-file edits are not allowed unless explicitly assigned.

## Event Protocol Additions

Add event types to `references/event-protocol.md` and runtime event writers:

- `coordinator.started`: coordinator registry record created and launch attempt started.
- `coordinator.completed`: coordinator process exited successfully or reported completion.
- `coordinator.failed`: coordinator launch or process failed.
- `agent.spawned`: any worker, reviewer, or validator is registered.
- `agent.heartbeat`: an agent heartbeat is recorded.
- `workstream.assigned`: a workstream is assigned to a registered implementation agent.
- `agent.completed`: an agent report is accepted into runtime state.
- `agent.failed`: an agent exits, reports failure, or misses the heartbeat timeout.
- `protocol.violation`: coordinator-only, file-scope, unregistered-agent, or state-contract violation detected.
- `decision.requested`: coordinator or runtime requested user input before continuing.

Existing events such as `run.created`, `plan.imported`, `workstream.planned`, `review.completed`, and `validation.completed` remain valid.

## Coordinator Launch Protocol

Add a `run` command in a staged implementation:

```bash
python3 scripts/de.py run <repo> --run-id <run-id> --dry-run
python3 scripts/de.py run <repo> --run-id <run-id> --provider codex --dry-run
python3 scripts/de.py run <repo> --run-id <run-id> --provider claude --dry-run
```

Defaults:

- If `--run-id` is omitted, use the latest run.
- If `--provider` is omitted, use `codex`.
- `--dry-run` is required for the first implementation wave that introduces the launcher.
- Dry-run does not start a provider process or mutate project files.
- Dry-run output must be deterministic enough for tests to assert provider, profile, executable, rendered arguments, prompt path marker, run id, and state directory.
- Dry-run may create no state, or it may write an explicitly marked preview under `.dispatch/runs/<run-id>/artifacts/`; implementation should choose the smaller testable behavior and document it.

Provider profiles resolve provider-specific command syntax. Exact prompt/input/context flags may be finalized during implementation after checking the installed CLI behavior, but the dry-run templates must still expose the intended command shape.

Codex default profile:

```json
{
  "provider": "codex",
  "profile": "codex-exec",
  "executable": "codex",
  "template": ["codex", "exec", "--cd", "{repo_root}", "Read and follow the Dispatch Engine coordinator instructions in this file: {prompt_path}"],
  "context": {
    "run_id": "{run_id}",
    "state_dir": "{state_dir}",
    "plan_path": "{plan_source}"
  }
}
```

Claude profile:

```json
{
  "provider": "claude",
  "profile": "claude-p",
  "executable": "claude",
  "template": ["claude", "-p", "Read and follow the Dispatch Engine coordinator instructions in this file: {prompt_path}"],
  "context": {
    "repo_root": "{repo_root}",
    "run_id": "{run_id}",
    "state_dir": "{state_dir}",
    "plan_path": "{plan_source}"
  }
}
```

Core runtime semantics must not depend on provider internals. Profiles only render commands, inject the coordinator protocol prompt, capture logs, and record lifecycle state.

## Coordinator Prompt Contract

The generated coordinator prompt must include:

- target repository path;
- run id and state directory;
- objective and imported plan summary;
- selected provider and provider profile;
- coordinator-only rule;
- allowed coordinator writes: `.dispatch/` state only;
- requirement to register workers, reviewers, and validators before treating their output as valid;
- required events and heartbeat cadence;
- workstream dependency and write-scope rules;
- decision request format;
- report format and expected report path.

The prompt must explicitly say that project implementation belongs to registered implementation agents, not the coordinator.

## Status Observability

Extend `de status` to report:

- run id, run status, objective, and state path;
- selected provider and coordinator profile when present;
- coordinator status and heartbeat freshness;
- counts by agent role;
- counts by agent status;
- active workstream assignments;
- completed, failed, blocked, and unassigned workstreams;
- pending decisions;
- protocol violation count;
- last event timestamp.

Human output should stay concise. JSON output should include structured `agents`, `agent_counts`, `workstream_assignments`, `heartbeat_summary`, `pending_decisions`, and `protocol_violations`.

## Protocol Violation Detection

Initial detection can be conservative:

- If a coordinator registry record has project paths in `assigned_files` or `allowed_write_roots`, emit `protocol.violation`.
- If a workstream is marked implemented or completed without a registered worker, reviewer, or validator as required by the plan, emit `protocol.violation`.
- If an implementation agent reports changed files outside its assigned file scope, emit `protocol.violation`.
- If project files changed during a coordinator-only dry-run or coordinator-only phase, emit `protocol.violation`.

The first implementation does not need perfect process-level attribution. It must record enough state and events to make violations visible and block acceptance until reviewed.

## Documentation Changes

Update:

- `references/orchestrator-loop.md`: add provider CLI coordinator launch as the next stage of the imported-plan loop.
- `references/event-protocol.md`: add `agents/`, `reports/`, `logs/`, `heartbeats/`, provider selection fields, and the new event types.
- `references/worker-protocol.md`: clarify registered implementation agents and coordinator-only behavior.
- `SKILL.md` and `README.md`: describe `de run`, default Codex provider behavior, explicit Claude provider support, and the direct-implementation prohibition.

## Workstream Sequencing

- `01-agent-state-protocol`: agent registry, lifecycle events, role rules, and protocol violation foundation.
- `02-status-observability`: `de status` and event readers for subagent counts, progress, heartbeats, decisions, provider/profile details, and violations.
- `03-run-launcher-dry-run`: adapter-neutral provider profiles and `de run --dry-run` command rendering for default Codex, explicit Codex, and explicit Claude.
- `04-docs-and-validation`: update references, skill docs, README, tests, grep checks, and status handoff.

## Testing and Validation

Run:

```bash
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py init . --plan .dispatch/plans/<plan-id>.json
python3 scripts/de.py run . --run-id <run-id> --dry-run
python3 scripts/de.py run . --run-id <run-id> --provider codex --dry-run
python3 scripts/de.py run . --run-id <run-id> --provider claude --dry-run
python3 scripts/de.py status .
python3 scripts/de.py status . --json
python3 scripts/de.py tail .
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

Manual checks:

- Omitted provider renders the same provider/profile as `--provider codex`.
- Claude dry-run renders a `claude -p` command shape without launching a process.
- Codex dry-run renders a `codex exec` command shape without launching a process.
- The dry-run launcher does not modify project files.
- Coordinator prompt states the coordinator-only rule.
- New durable docs include metadata.
- `de status` reports subagent counts from state, not chat memory.
- Protocol violations are visible in both events and status JSON.

## Risks and Follow-ups

- Risk: Provider CLIs may not expose enough process hooks for rich supervision. Mitigation: keep the core protocol file-based and adapter-neutral.
- Risk: Codex or Claude CLI arguments may differ by installed version. Mitigation: treat command templates as explicit dry-run surfaces whose final flags can be adjusted during implementation while preserving provider/profile behavior.
- Risk: The coordinator may still modify files if the provider process is run without sandbox constraints. Mitigation: use protocol prompts, phase checks, diff checks, and violation events before accepting work.
- Risk: Agent registry state may duplicate workstream state. Mitigation: keep workstream files as plan/progress truth and use agent files for execution identity, role, heartbeat, and report paths.
- Follow-up: Enable live process supervision after dry-run command rendering and state/event protocols are validated.
- Follow-up: Add external provider profile configuration files only when built-in `codex` and `claude` profiles are no longer enough.
