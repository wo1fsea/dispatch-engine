---
language: en-US
audience: agent
doc_type: spec
---

# Live Coordinator Supervision Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

`rfc-0005-provider-cli-coordinator-protocol` added:

- `de run --dry-run`;
- provider profiles for `codex` and `claude`;
- centralized coordinator prompt template under `references/prompts/`;
- `scripts/dispatch_engine/coordinators.py` for dry-run command rendering;
- `scripts/dispatch_engine/agents.py` for agent registry helpers;
- status observability for registered agents;
- event helpers for coordinator and agent lifecycle events, except live completion/failure are only documented vocabulary so far.

This spec makes `de run` without `--dry-run` perform a foreground provider process launch and record enough state to inspect the result.

## Change Gate

- Problem: Dry-run proves command shape but does not verify provider process supervision, log capture, or coordinator lifecycle state.
- Existing path considered: Continue using dry-run plus manual provider launch.
- Why existing path is insufficient: Manual launch does not create coordinator records, logs, prompt snapshots, or completion/failure events.
- Smallest new surface: Add foreground live launch to `de run`, prompt snapshots, coordinator registry updates, stdout/stderr capture, and completion/failure events.
- What will be deleted or replaced: Nothing. `--dry-run` remains supported.
- Owner: Dispatch Engine maintainers.
- Validation: Unit tests with fake `codex` and `claude` executables on `PATH`, CLI smoke checks, full unittest discovery, and `git diff --check`.
- Temporary or permanent: Permanent supervision foundation.
- Removal condition: Superseded only by a richer process manager preserving the same state/event semantics.

## Proposed Runtime Changes

### Run Directory

Extend new run initialization to include:

```text
.dispatch/runs/<run-id>/
  prompts/
    coordinator-001.md
  logs/
    coordinator-001.stdout.log
    coordinator-001.stderr.log
```

Legacy runs should create these directories lazily during live launch.

### Coordinator Launch

The live launch path sits next to the dry-run renderer:

```python
launch_run_coordinator(target, run_id=None, provider="codex") -> dict
```

Responsibilities:

- resolve target repo and run state dir;
- load `run.json`;
- render coordinator prompt through `scripts/dispatch_engine/prompts.py`;
- write the coordinator prompt snapshot to `prompts/coordinator-001.md`;
- render provider argv using a short instruction that points the provider to the prompt snapshot path;
- register `coordinator-001` with role `coordinator`, provider/profile, status `running`, prompt/log/report paths, and `.dispatch/` allowed writes;
- start the provider process in the target repository;
- capture stdout/stderr to log files;
- update coordinator status to `completed` or `failed`;
- emit `coordinator.started`, `coordinator.completed`, or `coordinator.failed`;
- return a structured payload for CLI output.

### Provider Command Shape

Codex live command should use the installed Codex CLI exec shape and pass a short instruction that names the recorded prompt snapshot:

```text
codex exec --sandbox danger-full-access --cd <repo-root> "Read and follow the Dispatch Engine coordinator instructions in this file: <prompt-file>"
```

Claude live command should use:

```text
claude --dangerously-skip-permissions --permission-mode bypassPermissions -p "Read and follow the Dispatch Engine coordinator instructions in this file: <prompt-file>"
```

Tests should create fake `codex` and `claude` executables in a temporary directory and prepend that directory to `PATH`.

### Event Additions

Live supervision uses event helpers for:

- `coordinator.started`
- `coordinator.completed`
- `coordinator.failed`

Payloads should include:

- `agent_id`;
- `provider`;
- `profile`;
- `exit_code`;
- `stdout_path`;
- `stderr_path`;
- optional failure reason.

### CLI

`de run` behavior:

- with `--dry-run`: existing dry-run output;
- without `--dry-run`: live launch;
- unsupported provider: non-zero error;
- missing run: non-zero error;
- missing executable: non-zero error and failure state if a run was resolved.

Human output should include provider/profile, run id, exit code, state dir, prompt path, stdout path, and stderr path.

JSON output should expose the same fields.

## Files

- `scripts/dispatch_engine/coordinators.py`
- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/events.py`
- `scripts/dispatch_engine/runs.py`
- `tests/test_live_coordinator_supervision.py`
- `references/event-protocol.md`
- `references/orchestrator-loop.md`
- `SKILL.md`
- `README.md`

## Testing and Validation

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py run <temp-repo> --provider codex
python3 scripts/de.py run <temp-repo> --provider claude
python3 scripts/de.py status <temp-repo> --json
python3 scripts/de.py tail <temp-repo>
git diff --check
```

Manual checks:

- Fake Codex receives the prompt snapshot path in argv.
- Fake Claude receives the prompt snapshot path in argv.
- The prompt snapshot file contains the rendered coordinator prompt.
- Prompt template remains centralized under `references/prompts/`.
- Live launch creates no runtime files outside `.dispatch/`.
- `de status` shows coordinator completion/failure through agent counts.

## Risks and Follow-ups

- Risk: Real provider CLIs may have version-specific argument differences. Mitigation: keep fake-CLI tests for supervision semantics and adjust provider profiles in a later compatibility pass if needed.
- Risk: Foreground execution blocks until provider exit. Mitigation: background supervision is a follow-up spec.
- Risk: Provider processes can still modify project files. Mitigation: coordinator-only prompt, `.dispatch/` state, and later protocol-violation diff checks.
- Follow-up: Add background mode.
- Follow-up: Add heartbeat timeout monitoring.
- Follow-up: Add process cancellation.
