---
language: en-US
audience: agent
doc_type: router
---

# Governance

This directory holds the detailed engineering governance workflows.

`AGENTS.md` is the canonical router. If files here are added, removed, renamed, or moved, update `AGENTS.md` in the same change.

## Local Profile

Dispatch Engine currently uses a strict governance profile because its core surface will include CLI commands, runtime state, event formats, worker adapters, validation behavior, and agent-facing instructions.

Prefer the smallest workflow that fits the task. Use specs and workstreams for ambiguous, cross-module, contract-affecting, or high-risk changes; keep narrow mechanical changes direct.
