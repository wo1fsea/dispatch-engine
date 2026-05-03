---
language: en-US
audience: mixed
doc_type: spec
---

# Live Coordinator Supervision Product Spec

## Summary

Dispatch Engine moves from provider dry-run rendering to live coordinator process supervision. `de run` without `--dry-run` launches the selected provider CLI coordinator from imported run state, registers the coordinator in `.dispatch/`, captures logs, emits lifecycle events, and reports completion or failure through status.

Codex remains the default provider. Claude remains supported explicitly. Live process supervision must preserve the coordinator-only boundary: the launched coordinator may write Dispatch Engine runtime state under `.dispatch/`, but project implementation still belongs to registered worker, reviewer, or validator agents.

## Goals / Non-goals

- Goal: Make `de run <repo>` launch a provider CLI coordinator instead of requiring `--dry-run`.
- Goal: Keep `--dry-run` available and unchanged for previewing commands.
- Goal: Default omitted provider selection to Codex.
- Goal: Support live Codex command shape based on `codex exec --sandbox danger-full-access`.
- Goal: Support live Claude command shape based on `claude --dangerously-skip-permissions --permission-mode bypassPermissions -p`.
- Goal: Register the coordinator agent before launch and update it on completion or failure.
- Goal: Write coordinator prompt snapshots and process logs under `.dispatch/runs/<run-id>/`.
- Goal: Pass the recorded coordinator prompt snapshot path to both Codex and Claude, instead of embedding the full prompt inline.
- Goal: Emit `coordinator.started`, `coordinator.completed`, and `coordinator.failed`.
- Goal: Make `de status` show live-run coordinator state through existing agent observability.
- Non-goal: Implement worker spawning, reviewer execution, validator execution, or scheduling algorithms.
- Non-goal: Run a long-lived daemon or background service.
- Non-goal: Implement cancellation, resume, retries, or timeout enforcement.
- Non-goal: Detect all possible project-file mutations by provider processes in this change.
- Non-goal: Require real Codex or Claude binaries in unit tests.

## Behavior Invariants

1. `de run <repo>` uses the latest imported run and provider `codex` by default.
2. `de run <repo> --run-id <id>` launches the selected coordinator for that run.
3. `de run <repo> --provider codex` launches the Codex profile.
4. `de run <repo> --provider claude` launches the Claude profile.
5. `de run <repo> --dry-run` still renders without launching or writing runtime state.
6. Live launch writes `.dispatch/runs/<run-id>/prompts/coordinator-001.md`.
7. Live launch registers `coordinator-001` under `.dispatch/runs/<run-id>/agents/` before starting the process.
8. Live launch writes `.dispatch/runs/<run-id>/logs/coordinator-001.stdout.log` and `.dispatch/runs/<run-id>/logs/coordinator-001.stderr.log`.
9. Live launch emits `coordinator.started` when the process is started.
10. A zero exit code marks the coordinator agent `completed` and emits `coordinator.completed`.
11. A non-zero exit code marks the coordinator agent `failed` and emits `coordinator.failed`.
12. Missing provider binaries fail clearly and record coordinator failure state when possible.
13. Live launch output includes provider, profile, run id, state dir, exit code, and log paths.
14. `de status` can report coordinator completed/failed/running state using existing agent registry data.
15. Tests use fake provider executables on `PATH`, not real Codex or Claude calls.

## States and Edge Cases

- No run exists.
- Explicit run id does not exist.
- Provider is omitted.
- Provider is `codex`.
- Provider is `claude`.
- Provider is unsupported.
- Provider executable is missing from `PATH`.
- Provider exits `0`.
- Provider exits non-zero.
- Provider writes stdout and stderr.
- A prompt snapshot already exists.
- A previous coordinator record exists for the run.
- The run is legacy and lacks `prompts/`, `logs/`, or `agents/`.

## Open Questions

- Should future live runs stream output while the coordinator is running, or only write log files after process completion?
- Should `de run` eventually support background mode, or should that be a separate command?
