---
language: en-US
audience: agent
doc_type: workstream
status: planned
updated: 2026-05-02
---

# 04 - Validation And Dogfood

## Scope

Validate the observation loop against a real or fixture target run:

1. Start a detached Dispatch Engine run.
2. Query status from a separate Codex-triggered check.
3. Confirm Codex can summarize material changes from `.dispatch/` state.
4. Confirm the fallback behavior when no heartbeat is configured.

## Acceptance

1. A detached run remains queryable without blocking the foreground chat.
2. A status check reports pending decisions and protocol violations from JSON
   state.
3. Validation records commands and residual risks.
