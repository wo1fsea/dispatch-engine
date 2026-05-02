---
language: en-US
audience: mixed
doc_type: spec
---

# Detached Coordinator Supervisor Product Spec

## Summary

Interactive Codex cannot remain conversational while it is blocked inside a
foreground `de run` process. Dispatch Engine needs a detached coordinator launch
mode that starts the provider coordinator in the background, returns
immediately, and leaves progress visible through `.dispatch/`, `de status`, and
`de tail`.

## Goals / Non-goals

- Goal: Add `de run --detach` for interactive operation.
- Goal: Record supervisor process state under `.dispatch/runs/<run-id>/supervisors/`.
- Goal: Keep foreground `de run` for debugging, tests, and CI-style smoke.
- Goal: Preserve coordinator-only boundaries and existing provider launch
  behavior.
- Non-goal: Build a long-running daemon, dashboard, scheduler, or stop/restart
  manager.
- Non-goal: Change worker/reviewer/validator spawn semantics.

## User Outcome

An operator can start Dispatch Engine from an interactive Codex session and keep
talking with the user while the provider coordinator runs. The operator can poll
`de status` and `de tail` instead of waiting for the provider process to exit.

## Acceptance

1. `de run <repo> --detach` returns immediately with supervisor pid and paths.
2. Detached launch writes supervisor state under `.dispatch/runs/<run-id>/supervisors/`.
3. The supervisor records coordinator completion or failure through the same
   agent/event/log contract as foreground launch.
4. `de status --json` exposes supervisor status.
5. Tests prove a slow provider keeps running after the parent command returns.
