---
workstream_id: 03-run-launcher-dry-run
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker C
branch: ""
updated: 2026-05-02
depends_on:
  - 01-agent-state-protocol
---

# Run Launcher Dry Run

## Scope

Add an adapter-neutral coordinator launcher surface with dry-run support for Codex and Claude provider CLI coordinators.

## Files

- `scripts/dispatch_engine/cli.py`
- optional new module: `scripts/dispatch_engine/coordinators.py`
- optional prompt/template file under `references/` or `scripts/dispatch_engine/`
- `tests/`

## Requirements

- Add `de run <repo> --run-id <run-id> --dry-run`; it must default to provider `codex`.
- Add `de run <repo> --run-id <run-id> --provider codex --dry-run`.
- Add `de run <repo> --run-id <run-id> --provider claude --dry-run`.
- Default to latest run when `--run-id` is omitted.
- Resolve Codex to a `codex exec --sandbox danger-full-access` command shape with prompt/input/context arguments to be finalized by implementation.
- Resolve Claude to a `claude --dangerously-skip-permissions --permission-mode bypassPermissions -p` command shape with prompt/input/context arguments to be finalized by implementation.
- Make provider command templates explicit enough for dry-run tests to assert executable, provider, profile, run id, state directory, and prompt source.
- Generate a coordinator protocol prompt that states coordinator-only behavior and registered implementation-agent requirements.
- Keep runtime prompt text in `references/prompts/`; runtime code should load and render templates from there.
- Show resolved command, prompt location or prompt preview, run id, provider, coordinator profile, and expected state/event actions.
- Ensure dry-run does not launch a provider process or modify project files.
- Report missing run, unsupported provider, malformed template, and missing provider binary clearly.

## Validation

```bash
python3 scripts/de.py run . --run-id <run-id> --dry-run
python3 scripts/de.py run . --run-id <run-id> --provider codex --dry-run
python3 scripts/de.py run . --run-id <run-id> --provider claude --dry-run
python3 scripts/de.py run . --provider unknown --dry-run
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

Evidence:

- `PYTHONPATH=scripts python3 -m unittest tests.test_run_dry_run` failed first because `dispatch_engine.coordinators` did not exist, then passed after implementation.
- `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed: 30 tests.
- CLI smoke checks passed for default Codex, explicit Codex, explicit Claude, unsupported provider, and missing run.
- `git diff --check` passed.

## Activity Log

- 2026-05-02 Worker C: validated `de run --dry-run` provider rendering with focused tests, full unittest discovery, CLI smokes, and `git diff --check`.
- 2026-05-02 Worker C: claimed workstream and began test-first implementation of `de run --dry-run` provider rendering.
- 2026-05-02 Worker S: initialized workstream as ready.
