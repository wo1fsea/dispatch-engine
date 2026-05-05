---
workstream_id: 02-coordinator-ready-set
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - references/prompts/coordinator-protocol.md
  - references/orchestrator-loop.md
  - specs/rfc-0025-safe-parallel-dispatch-contract/
depends_on:
  - 01-parallelism-contract
updated: 2026-05-06
---

# Workstream 02: Coordinator Ready Set

Update the coordinator prompt so the provider coordinator performs a ready-set
pass before every dispatch cycle and batch-spawns safe workstreams.

Required behavior:

- Compute ready workstreams from dependencies, blockers, capability warnings,
  active agents, and write-scope conflicts.
- Spawn all safe ready workers up to the concurrency budget.
- Record dispatch batches and active concurrency in the coordinator report.
- Record a concrete serial rationale for every ready workstream not spawned.
- Preserve coordinator-only behavior and provider-native spawn ownership.

Validation:

```bash
rg -n "ready set|ready workstream|batch-spawn|concurrency budget|serial rationale" references/prompts/coordinator-protocol.md references/orchestrator-loop.md
git diff --check
```
