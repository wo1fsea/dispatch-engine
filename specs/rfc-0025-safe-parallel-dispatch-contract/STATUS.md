---
spec_id: rfc-0025-safe-parallel-dispatch-contract
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/22
updated: 2026-05-06
---

# Status

## Summary

Ready for review. The safe parallel dispatch contract now has routing-level
operator guidance, coordinator ready-set/batch-spawn guidance, warning-only
plan diagnostics, and integration validation evidence. Dispatch Engine remains
skill-first: diagnostics inform coordinator judgment without replacing it with
a deterministic runtime scheduler.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Skill, operator, and plan authoring parallelism contract | validated | worker-006 |  |  | 2026-05-06 |
| 02 | Coordinator prompt ready-set and batch-spawn contract | validated | worker-003 |  | 01 | 2026-05-06 |
| 03 | Warning-only plan diagnostics and validation, if needed | validated | worker-003 |  | 01 | 2026-05-06 |
| 04 | Docs, dogfood fixture, and acceptance evidence | validated | worker-006 |  | 02, 03 | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: investigated rfc-0024 run
  `20260505T095306005146Z`; found every workstream marked `mode: serial` with
  a full dependency chain and broad shared write scopes.
- 2026-05-06 codex: filed GitHub issue #22 for the dogfood framework problem.
- 2026-05-06 codex: created this ready spec to define a safe parallel dispatch
  contract without adding a runtime scheduler first.
- 2026-05-06 worker-003: implemented warning-only plan diagnostics for
  accidental under-parallelization and updated coordinator ready-set guidance
  for batch spawning, concurrency budget use, and serial rationale evidence.
- 2026-05-06 worker-006: reconciled routing docs and validated the integrated
  issue #22 implementation with the full required command suite.

## Spec Handoff

- Spec path: `specs/rfc-0025-safe-parallel-dispatch-contract`
- Status: ready-review
- Spec type: skill/prompt/runtime-diagnostic process correction
- Open questions: future status shape for `ready_but_serialized` if warning-only
  diagnostics prove insufficient in dogfood
- Workstreams: `01-parallelism-contract`, `02-coordinator-ready-set`,
  `03-plan-diagnostics`, `04-docs-dogfood-validation`
- Next owner: main-session review
- Validation expectation: docs grep, prompt review, optional focused
  plan-diagnostic tests, full unittest discovery if runtime code changes,
  dry-run/dogfood evidence with at least one parallel worker batch
- Ready to review: yes
