---
spec_id: rfc-0025-safe-parallel-dispatch-contract
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/22
updated: 2026-05-06
---

# Status

## Summary

Ready. Created from dogfood issue #22 after the rfc-0024 dashboard run proved
that the current plan/prompt path can serialize every workstream. The spec keeps
Dispatch Engine skill-first: fix planning and coordinator guidance first, add
warning-only runtime diagnostics only if needed, and do not replace coordinator
judgment with a deterministic scheduler.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Skill, operator, and plan authoring parallelism contract | ready |  |  |  | 2026-05-06 |
| 02 | Coordinator prompt ready-set and batch-spawn contract | ready |  |  | 01 | 2026-05-06 |
| 03 | Warning-only plan diagnostics and validation, if needed | ready |  |  | 01 | 2026-05-06 |
| 04 | Docs, dogfood fixture, and acceptance evidence | ready |  |  | 02, 03 | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: investigated rfc-0024 run
  `20260505T095306005146Z`; found every workstream marked `mode: serial` with
  a full dependency chain and broad shared write scopes.
- 2026-05-06 codex: filed GitHub issue #22 for the dogfood framework problem.
- 2026-05-06 codex: created this ready spec to define a safe parallel dispatch
  contract without adding a runtime scheduler first.

## Spec Handoff

- Spec path: `specs/rfc-0025-safe-parallel-dispatch-contract`
- Status: ready
- Spec type: skill/prompt/runtime-diagnostic process correction
- Open questions: default provider concurrency budget; status shape for
  `ready_but_serialized`; whether diagnostics live in `de init` or a future
  explicit command
- Workstreams: `01-parallelism-contract`, `02-coordinator-ready-set`,
  `03-plan-diagnostics`, `04-docs-dogfood-validation`
- Next owner: implementation agents with main-session review
- Validation expectation: docs grep, prompt review, optional focused
  plan-diagnostic tests, full unittest discovery if runtime code changes,
  dry-run/dogfood evidence with at least one parallel worker batch
- Ready to implement: yes
