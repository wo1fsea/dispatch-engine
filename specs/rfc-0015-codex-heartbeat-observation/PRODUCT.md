---
language: en-US
audience: mixed
doc_type: spec
---

# Codex Heartbeat Observation Product Spec

## Summary

`de run --detach` keeps interactive Codex from blocking on the coordinator
process, but it does not make the foreground chat aware of background progress
by itself. Dispatch Engine needs an explicit observation contract: the runtime
writes durable, Codex-readable state; interactive Codex reads and explains that
state when the user asks or when the Codex host wakes the current thread through
a heartbeat automation.

The Dispatch Engine CLI is Codex-facing, not a human control panel. Human
interaction stays in the outer Codex chat. CLI commands and `.dispatch/` files
must therefore be stable, scriptable, and JSON-first so Codex can interpret
status, decisions, alerts, and protocol violations for the user.

## Goals / Non-goals

- Goal: Record that foreground Codex awareness requires either a user message
  or a Codex host heartbeat/wakeup.
- Goal: Define heartbeat observation as a host-layer mechanism, not a Dispatch
  Engine daemon responsibility.
- Goal: Keep `de` commands Codex-facing and JSON-first.
- Goal: Define the next Codex-facing surfaces for status interpretation,
  decision resolution, events, and alerts.
- Goal: Require skill/operator guidance for starting a detached run with an
  optional thread heartbeat monitor when the host supports it.
- Non-goal: Build a human dashboard or terminal UI.
- Non-goal: Make Dispatch Engine send chat messages directly.
- Non-goal: Assume every Codex host supports heartbeat automation.
- Non-goal: Move repository discovery, planning judgment, or user conversation
  into the runtime.

## User Outcome

After interactive Codex starts a detached Dispatch Engine run, the user has an
honest progress model:

- If the host supports heartbeat automation, Codex can wake this thread on a
  schedule, read Dispatch Engine state, and report material changes.
- If no heartbeat is configured, Codex can still report the latest state when
  the user asks.
- Dispatch Engine remains the source of durable truth through `.dispatch/` and
  JSON CLI output.

## Operating Model

```text
user <-> interactive Codex chat
              |
              | creates plan, starts detached run, optionally creates heartbeat
              v
        de run --detach
              |
              v
       provider coordinator -> spawned workers/reviewers/validators
              |
              v
     .dispatch/runs/<run-id>/ durable state
              ^
              |
heartbeat wakeup or user question -> Codex reads de status/events/alerts --json
                                  -> Codex explains progress and asks decisions
```

## Acceptance

1. The spec and skill guidance state that `de` is Codex-facing, not the user UI.
2. The spec states that detached execution does not by itself wake interactive
   Codex.
3. The spec defines heartbeat automation as the preferred host-layer wakeup
   mechanism when available.
4. The spec defines fallback behavior when no heartbeat exists: Codex checks
   status on the next user message.
5. The spec identifies required future runtime surfaces:
   `status --json`, event delta reads, alert snapshots, and decision resolution
   by machine-readable command.
6. Existing docs avoid implying that the foreground chat continuously polls
   without a host wakeup.
