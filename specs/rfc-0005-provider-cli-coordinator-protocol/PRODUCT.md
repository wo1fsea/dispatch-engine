---
language: en-US
audience: mixed
doc_type: spec
---

# Provider CLI Coordinator Protocol Product Spec

## Summary

Dispatch Engine should be able to launch and supervise provider CLI coordinators such as `codex exec --sandbox danger-full-access` and `claude --dangerously-skip-permissions --permission-mode bypassPermissions -p` while preserving the architecture boundary from `rfc-0004-explicit-plan-orchestrator-boundary`.

The provider CLI process is a coordinator agent, not an implementation shortcut. It may plan, dispatch, monitor, review, summarize, request decisions, and write Dispatch Engine runtime state under `.dispatch/`. It must not directly edit project files to implement the requested change. Project implementation must happen through registered worker, reviewer, or validator agents whose activity is visible in Dispatch Engine state, status output, and events.

Codex is the default coordinator provider. When the operator runs `de run <repo> --run-id <id>` without a provider, Dispatch Engine uses the Codex provider profile. Operators may explicitly choose `--provider codex` or `--provider claude`; both provider command shapes must be dry-run renderable before real process supervision is required.

## Goals / Non-goals

- Goal: Define an adapter-neutral protocol for launching provider CLI coordinators.
- Goal: Support Codex and Claude CLI coordinator providers in the command surface.
- Goal: Default omitted provider selection to Codex.
- Goal: Make coordinator-only behavior explicit and enforceable through prompts, state, status, and violation events.
- Goal: Add durable agent registry state under `.dispatch/runs/<run-id>/agents/`.
- Goal: Track coordinator, worker, reviewer, and validator progress through reports, logs, heartbeats, and events.
- Goal: Make `de status` report subagent counts and progress from durable state.
- Goal: Keep provider-specific command details at the launcher/profile layer, not in core orchestration semantics.
- Non-goal: Turn Dispatch Engine into a provider-specific agent implementation.
- Non-goal: Let a coordinator directly implement project-file changes.
- Non-goal: Define final Codex or Claude CLI argument lists before implementation verifies the installed CLI versions.
- Non-goal: Define a full remote daemon, dashboard, queue, or database.
- Non-goal: Replace the explicit dispatch plan contract from `rfc-0004`.
- Non-goal: Implement provider-specific worker APIs in this stage.

## Behavior Invariants

1. Dispatch Engine launches a provider CLI coordinator from imported run state, not from repository inspection or heuristic planning.
2. `de run <repo> --run-id <id>` defaults to provider `codex`.
3. `de run <repo> --run-id <id> --provider codex` uses a Codex CLI coordinator command shape based on `codex exec --sandbox danger-full-access`, with prompt, input, context, and state arguments finalized by implementation.
4. `de run <repo> --run-id <id> --provider claude` uses a Claude CLI coordinator command shape based on `claude --dangerously-skip-permissions --permission-mode bypassPermissions -p`, with prompt, input, context, and state arguments finalized by implementation.
5. Provider command templates or config are explicit enough for dry-run tests to assert the selected executable, provider, prompt source, run id, and state path without launching a process.
6. A coordinator process is registered in `.dispatch/runs/<run-id>/agents/` before it receives work.
7. The coordinator role is `coordinator`; implementation roles are `worker`, `reviewer`, and `validator`.
8. The coordinator may plan, dispatch, monitor, review, summarize, request decisions, and write `.dispatch/` runtime state.
9. The coordinator must not directly edit project files to satisfy the objective.
10. Any project-file implementation change must be attributable to an observable registered worker, reviewer, or validator agent.
11. Dispatch Engine records every launched or declared subagent before treating its work as valid.
12. Dispatch Engine emits coordinator and agent lifecycle events, including `coordinator.started`, `agent.spawned`, `agent.heartbeat`, `workstream.assigned`, `agent.completed`, `agent.failed`, `protocol.violation`, and `decision.requested`.
13. `de status` reports run progress, coordinator status, subagent counts by role and status, workstream assignment/completion counts, heartbeat freshness, pending decisions, and protocol violations.
14. Provider-specific launch syntax is isolated behind provider profiles or explicit launcher arguments.
15. A provider CLI coordinator receives a protocol prompt that states the coordinator-only boundary and the requirement to register implementation agents.
16. If Dispatch Engine detects project-file changes without a registered implementation agent, it records `protocol.violation` and marks the run blocked until reviewed.
17. Heartbeats and reports are durable enough for another interactive Codex session to resume monitoring without relying on chat memory.
18. Dry-run launch mode shows the resolved provider command, protocol prompt path, expected state writes, and event plan without starting a provider process.
19. The first implementation wave may support dry-run rendering for both Codex and Claude before enabling real coordinator process supervision.

## States and Edge Cases

- A run exists from `de init --plan` but has no agent registry yet.
- `de run` is invoked without a run id; Dispatch Engine selects the latest run.
- `de run` is invoked without `--provider`; Dispatch Engine selects Codex.
- `de run` is invoked with `--provider codex`.
- `de run` is invoked with `--provider claude`.
- `de run` is invoked with an unsupported provider.
- `de run` is invoked with a missing run id.
- A provider command template is malformed.
- A provider CLI binary is missing from `PATH`.
- A dry-run render is requested on a machine without the provider CLI installed.
- A provider CLI process exits before its first heartbeat.
- A provider CLI process exits successfully but no worker, reviewer, or validator agents were registered for a workstream that required project-file changes.
- A coordinator requests a user decision before assigning blocked work.
- A coordinator attempts or appears to attempt project-file changes directly.
- A registered worker stops heartbeating.
- A worker completes but no reviewer or validator evidence exists.
- A reviewer rejects worker output.
- A validator fails validation.
- A run has multiple active workers in parallel.
- A worker reports changed files outside its assigned workstream scope.
- Legacy runs exist without `agents/`, `reports/`, `logs/`, or `heartbeats/`.

## Open Questions

None blocking. This spec is ready to implement with an initial dry-run launcher for both Codex and Claude, followed by durable state protocol and real process supervision.
