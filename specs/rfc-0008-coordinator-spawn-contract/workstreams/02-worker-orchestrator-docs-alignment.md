---
workstream_id: 02-worker-orchestrator-docs-alignment
language: en-US
audience: agent
doc_type: workstream
status: ready
owner: unassigned
branch: main
updated: 2026-05-02
depends_on:
  - 01-coordinator-spawn-prompt-contract
---

# Worker Orchestrator Docs Alignment

## Scope

Align operator and protocol docs with the coordinator-spawn contract.

## Files

- `README.md`
- `SKILL.md`
- `references/worker-protocol.md`
- `references/orchestrator-loop.md`
- `references/event-protocol.md` if event vocabulary needs clarification
- `specs/README.md`

## Requirements

- Avoid implying DE must launch implementation workers itself.
- State that coordinator-spawned and adapter-spawned workers share the same `.dispatch/` contract.
- Keep rfc-0007 helper-first worker evidence requirements intact.
- Keep provider-native coordinator spawn as the baseline; add runtime helpers
  only where dogfood proves durable state updates are too error-prone to write
  directly.

## Validation

```bash
rg "coordinator-spawn|provider-native|agent.spawned|workstream.assigned|worker report|registered worker" README.md SKILL.md references specs/rfc-0008-coordinator-spawn-contract
git diff --check
```
