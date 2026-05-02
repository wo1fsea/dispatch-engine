---
language: en-US
audience: agent
doc_type: spec
---

# Worker Adapter Protocol Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

`rfc-0006-live-coordinator-supervision` added:

- live foreground `de run`;
- default Codex and explicit Claude provider coordinator launch;
- coordinator prompt snapshots under `.dispatch/runs/<run-id>/prompts/`;
- stdout/stderr capture under `.dispatch/runs/<run-id>/logs/`;
- coordinator lifecycle state and `coordinator.started` / `coordinator.completed` / `coordinator.failed` events.

The remaining gap is worker observability. The coordinator prompt says implementation must be performed by registered implementation agents, but the runtime does not yet provide a concrete worker adapter protocol, worker prompt template, or worker report validation path.

## Change Gate

- Problem: The coordinator can be launched, but there is no stable way to register worker execution and accept its evidence.
- Existing path considered: Let the provider coordinator write ad hoc files under `.dispatch/`.
- Why existing path is insufficient: Ad hoc state would make `de status`, protocol violations, reviewer handoff, and future parallel scheduling fragile.
- Smallest new surface: Add worker protocol helpers, a centralized worker prompt template, report validation, status visibility, and tests using fake workers.
- What will be deleted or replaced: No existing runtime behavior should be removed.
- Owner: Dispatch Engine maintainers.
- Validation: focused unit tests, full unittest discovery, docs grep, CLI smoke checks, and `git diff --check`.
- Temporary or permanent: Permanent worker-observability foundation.
- Removal condition: Superseded only by a richer adapter manager preserving the same state/report/event semantics.

## Proposed Runtime Changes

### Worker Registry

Extend existing agent registry usage for implementation agents.

Required worker record fields:

```json
{
  "schema_version": 1,
  "agent_id": "worker-001",
  "role": "worker",
  "provider": "codex",
  "profile": "codex-exec",
  "status": "running",
  "run_id": "<run-id>",
  "workstream": "01-implementation",
  "assigned_files": ["src/example.py", "tests/test_example.py"],
  "allowed_write_roots": ["src/", "tests/"],
  "prompt_path": ".dispatch/runs/<run-id>/prompts/worker-001.md",
  "report_path": ".dispatch/runs/<run-id>/reports/worker-001.json",
  "stdout_path": ".dispatch/runs/<run-id>/logs/worker-001.stdout.log",
  "stderr_path": ".dispatch/runs/<run-id>/logs/worker-001.stderr.log",
  "log_path": ".dispatch/runs/<run-id>/logs/worker-001.jsonl"
}
```

Status vocabulary:

- `registered`
- `running`
- `blocked`
- `completed`
- `failed`

### Worker Report

Worker reports live under `reports/<agent-id>.json`.

Required report fields:

```json
{
  "schema_version": 1,
  "agent_id": "worker-001",
  "role": "worker",
  "workstream": "01-implementation",
  "status": "completed",
  "summary": "Implemented the scoped change.",
  "changed_files": ["src/example.py", "tests/test_example.py"],
  "validation": [
    {
      "command": "PYTHONPATH=scripts python3 -m unittest discover -s tests",
      "status": "passed",
      "summary": "All tests passed."
    }
  ],
  "questions": [],
  "blockers": [],
  "risks": []
}
```

Report statuses:

- `completed`
- `completed_with_concerns`
- `blocked`
- `failed`

### Worker Prompt Template

Add a centralized prompt template:

```text
references/prompts/worker-protocol.md
```

The template must include:

- target repository path;
- run id and state directory;
- workstream id/title/scope;
- assigned files and allowed write roots;
- dependency and parallel context;
- validation expectations;
- requirement that the worker is not alone in the codebase;
- requirement to avoid unassigned files unless a recorded decision expands scope;
- report path and report JSON shape;
- instruction to write runtime artifacts under `.dispatch/` only.

Runtime modules should load and render this template through `scripts/dispatch_engine/prompts.py`; worker prompt text must not be embedded inline in Python code.

### Worker Adapter Surface

First implementation may choose either:

1. protocol helpers only, with tests directly registering/completing workers; or
2. a minimal foreground fake-provider launch helper comparable to coordinator live launch.

The preferred MVP is helper-first:

```python
register_worker(run_state_dir, agent_id, provider, profile, workstream, assigned_files, allowed_write_roots) -> dict
write_worker_prompt(run_state_dir, agent_id, prompt_text) -> Path
complete_worker(run_state_dir, agent_id, report) -> dict
fail_worker(run_state_dir, agent_id, reason) -> dict
validate_worker_report(run_state_dir, agent_id) -> list[dict]
```

CLI exposure can wait unless needed for dogfooding. If a CLI is added, keep it narrow and state-oriented, not a scheduler:

```bash
python3 scripts/de.py worker register <repo> --run-id <run-id> --workstream <id> --agent-id <id>
python3 scripts/de.py worker complete <repo> --run-id <run-id> --agent-id <id> --report <path>
```

### Events

Use existing event helpers or add missing helpers for:

- `agent.spawned`
- `workstream.assigned`
- `agent.heartbeat`
- `agent.completed`
- `agent.failed`
- `protocol.violation`

`agent.completed` payload should include `agent_id` and `report_path`.

### Status and Violations

`de status` should continue to show:

- agent counts by role;
- agent counts by status;
- coordinator summary;
- workstream assignments;
- heartbeat summary;
- protocol violation count.

Add or harden violations:

- `missing_worker_report`: worker status is completed but report file is missing.
- `malformed_worker_report`: worker report is invalid JSON or missing required fields.
- `out_of_scope_changed_file`: worker report declares changed files outside assigned files/allowed write roots.
- `unregistered_implementation_completion`: workstream is implemented/completed without a valid implementation-agent report.

Scope matching for rfc-0007 can be conservative:

- exact match against `assigned_files`, or
- prefix match against `allowed_write_roots`.

## Files

- `references/prompts/worker-protocol.md`
- `references/worker-protocol.md`
- `references/event-protocol.md`
- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/prompts.py`
- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/events.py`
- `scripts/dispatch_engine/runs.py`
- `tests/test_worker_adapter_protocol.py`
- `README.md`
- `SKILL.md`

## Workstreams

1. `01-worker-state-report-protocol`: worker registration/report helpers and report validation.
2. `02-worker-prompt-template`: centralized worker prompt template and prompt rendering tests.
3. `03-status-violations`: status visibility and protocol violations for worker reports/scope.
4. `04-docs-validation`: update references, README/SKILL, and validation evidence.

## Testing and Validation

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py status <temp-repo> --json
rg "worker|worker-protocol|agent.spawned|workstream.assigned|protocol.violation|reports/" README.md SKILL.md references specs/rfc-0007-worker-adapter-protocol
git diff --check
```

Manual checks:

- Worker prompt template lives in `references/prompts/`.
- Worker reports live under `.dispatch/runs/<run-id>/reports/`.
- Worker prompt snapshots live under `.dispatch/runs/<run-id>/prompts/`.
- Worker logs live under `.dispatch/runs/<run-id>/logs/`.
- Coordinator-only boundaries are not weakened.
- Runtime-generated non-project files remain under `.dispatch/`.

## Risks and Follow-ups

- Risk: Worker protocol becomes too ceremonial before real worker execution exists. Mitigation: helper-first implementation and fake-worker tests.
- Risk: Scope checking is too naive. Mitigation: start conservative and document prefix/exact semantics before adding glob support.
- Risk: Coordinator writes worker reports itself and masks direct implementation. Mitigation: require durable worker identity, assigned scope, and report evidence; future diff attribution can harden this.
- Follow-up: Add reviewer adapter protocol.
- Follow-up: Add validator report protocol.
- Follow-up: Add coordinator-facing helper commands only where dogfood proves
  durable state updates are too error-prone to write directly.
- Follow-up: Harden safe parallel dispatch guidance once single-worker evidence
  is stable.
