---
language: en-US
audience: mixed
doc_type: spec
---

# Dashboard Observer Lifecycle Product Spec

## Summary

Dashboard observer processes must have a clear lifecycle when a run completes,
fails, is cancelled, or is superseded by a continuation run. Interactive Codex
should not keep showing a stale dashboard for an old run without an explicit
stale/superseded signal.

This spec covers GitHub issue #23.

## Goals / Non-goals

- Goal: Define how the skill launches, reuses, reports, and retires dashboard
  observers for detached DE runs.
- Goal: Surface terminal, stale, cancelled, and superseded run state in the
  dashboard and operator guidance.
- Goal: Ensure the host heartbeat remains the source of operator wakeups while
  the dashboard remains a read-only observer.
- Goal: Make continuation runs prefer opening or reporting the new run's
  dashboard instead of silently retaining an old tab.
- Non-goal: Make the dashboard responsible for driving decisions or heartbeats.
- Non-goal: Kill arbitrary user-started dashboard servers without evidence that
  they belong to the superseded run.

## Behavior Invariants

1. After `de run --detach`, interactive Codex starts or reuses a dashboard for
   the active run and reports the URL.
2. When a run reaches `completed`, `failed`, or `cancelled`, the dashboard shows
   terminal state and stops implying live progress.
3. When a new continuation run supersedes an old run, the old dashboard should
   be labeled stale/superseded or the operator should be guided to the new URL.
4. The host heartbeat is mandatory for detached supervision and stops when the
   terminal run state is reported; dashboard observer state does not replace it.
5. Dashboard process metadata lives under `.dispatch/`, not in project files.

## User Experience

- Codex can say which dashboard URL is current.
- If the in-app browser points to an old dashboard, the page itself indicates
  terminal or superseded state clearly.
- Restarting a dashboard is a normal operator action, not a manual recovery
  mystery.

## Open Questions

- Should `de dashboard` expose `--stop-run-observers` now, or is stale labeling
  enough for the next dogfood pass?
- Should observer metadata include browser-open status, or only server process
  metadata?
