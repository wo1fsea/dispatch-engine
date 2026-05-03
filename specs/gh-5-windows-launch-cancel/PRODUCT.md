---
spec_id: gh-5-windows-launch-cancel
language: en-US
audience: mixed
doc_type: spec
status: planned
created: 2026-05-04
updated: 2026-05-04
issue: https://github.com/wo1fsea/dispatch-engine/issues/5
---

# Windows Launch And Cancel Product Spec

## Summary

Dispatch Engine should operate the same Codex-facing runtime loop on Windows as
it does on POSIX hosts. Current Windows dogfood and local tests show that
provider launch and cancellation can fail even when the executable exists or
when a run should be safely marked cancelled.

## Goals / Non-goals

- Goal: Use the resolved provider executable path for live coordinator launch
  while preserving the rendered provider argv for dry-run, audit, and status
  output.
- Goal: Make foreground and detached fake-provider tests pass on Windows by
  using Windows-launchable fake provider executables.
- Goal: Treat invalid, missing, or already-exited Windows process ids as not
  running during cancellation instead of crashing.
- Goal: Normalize path assertions and path-like runtime output in tests so
  Windows separators do not cause false failures.
- Goal: Keep `de run --dry-run` behavior stable and non-mutating.
- Non-goal: Change the provider command contract or remove the high-permission
  Codex/Claude coordinator profiles.
- Non-goal: Fix GitHub issue #4 worker report schema conflicts in this spec;
  that is a separate protocol contract issue.
- Non-goal: Add a Windows service, daemon, installer, or shell-specific
  provider adapter.

## Behavior Invariants

1. `de run --dry-run --json` reports the provider command as the human-auditable
   command shape, including `argv`, `executable`, `executable_path`, and
   `executable_found`.
2. Live coordinator launch invokes the resolved executable path returned by
   the preflight lookup when one exists.
3. The persisted and returned `argv` remains the rendered provider command
   shape and does not leak temporary fake-provider implementation details.
4. If the provider executable is missing, live launch still records a durable
   failed coordinator state and a clear failure reason.
5. On Windows, tests that need a fake provider use an executable file shape that
   Windows can launch from `PATH`.
6. `de cancel` treats Windows liveness errors such as invalid PID handle/state
   as not running when no signal can be safely sent.
7. Cancellation still marks the run, supervisor, and active agents cancelled
   when process state is stale or already gone.
8. Prompt-template and runtime path checks compare path parts or normalized
   paths, not hard-coded POSIX separators.

## Acceptance

1. Focused live coordinator tests pass on Windows.
2. Focused detached coordinator tests pass on Windows.
3. Copied skill install E2E passes on Windows.
4. Cancel control tests cover Windows liveness error handling and pass.
5. Prompt-template path tests pass on Windows and POSIX.
6. Full unittest discovery passes with `PYTHONPATH=scripts`.
7. `python scripts/de.py --help`, `version`, `run --help`, `cancel --help`, and
   `stop --help` still pass.
8. Docs and spec status record the Windows validation evidence and keep issue
   #4 explicitly out of scope.

