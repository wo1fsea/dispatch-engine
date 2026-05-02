---
spec_id: rfc-0008-coordinator-spawn-contract
language: en-US
audience: agent
doc_type: spec
status: validated
implementation: completed
validation: passed
coordinator: dispatch-engine
updated: 2026-05-02
---

# Status

## Summary

Validated. This spec corrects the next-step architecture after rfc-0007: the provider coordinator owns subagent spawn decisions, while Dispatch Engine owns the durable registration, prompt snapshot, heartbeat, report, event, status, and violation contract.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Coordinator spawn prompt contract | validated | codex | main |  | 2026-05-02 |
| 02 | Worker/orchestrator docs alignment | validated | codex | main | 01 | 2026-05-02 |
| 03 | Validation and handoff | validated | codex | main | 01, 02 | 2026-05-02 |

## Activity Log

- 2026-05-02 codex: created ready RFC after product discussion clarified that coordinator-spawned workers should be registered in `.dispatch/`, not launched by DE by default.
- 2026-05-02 codex: centralized coordinator prompt snapshot/path-instruction helpers in `scripts/dispatch_engine/prompts.py`, confirmed live launch uses prompt-file instructions, aligned README/SKILL references, and validated with focused tests, CLI smoke checks, prompt/docs grep, and `git diff --check`.
- 2026-05-02 codex: after adjacent RFCs landed, full `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed in integration review.

## Spec Handoff

- Spec path: `specs/rfc-0008-coordinator-spawn-contract`
- Status: validated
- Spec type: architecture/protocol prompt contract
- Open questions: CLI helper commands for coordinator use; generated vs coordinator-supplied agent ids; whether status distinguishes coordinator-spawned from operator-registered agents
- Workstreams: `01-coordinator-spawn-prompt-contract`, `02-worker-orchestrator-docs-alignment`, `03-validation-handoff`
- Next owner: maintainer review / dogfood
- Validation expectation: full unittest discovery, CLI smoke checks, prompt/docs grep, `git diff --check`
- Ready to implement: completed
