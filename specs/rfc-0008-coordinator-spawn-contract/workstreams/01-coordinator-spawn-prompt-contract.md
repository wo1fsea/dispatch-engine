---
workstream_id: 01-coordinator-spawn-prompt-contract
language: en-US
audience: agent
doc_type: workstream
status: ready
owner: unassigned
branch: main
updated: 2026-05-02
depends_on: []
---

# Coordinator Spawn Prompt Contract

## Scope

Update the coordinator prompt contract so coordinator-spawned subagents must be registered, scoped, tracked, and reported through `.dispatch/`.

## Files

- `references/prompts/coordinator-protocol.md`
- `tests/test_run_dry_run.py` or prompt-focused tests if existing assertions need updates

## Requirements

- State that coordinator may spawn workers/reviewers/validators using provider-native mechanisms.
- Require spawned agents to be registered before assignment.
- Require worker prompt snapshots, reports, heartbeats/status, lifecycle events, and validation evidence.
- Require valid implementation-agent reports before output is accepted.
- Preserve the coordinator-only prohibition on direct project-file implementation.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg "spawn|agent.spawned|workstream.assigned|registered worker|provider-native" references/prompts/coordinator-protocol.md
git diff --check
```
