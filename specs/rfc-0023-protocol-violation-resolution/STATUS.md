---
spec_id: rfc-0023-protocol-violation-resolution
language: en-US
audience: agent
doc_type: spec
status: done
implementation: implemented
validation: passed
issue: https://github.com/wo1fsea/dispatch-engine/issues/19
updated: 2026-05-04
---

# Status

## Summary

Done. Created from dogfood issue #19 to add an explicit, durable way to
acknowledge or supersede protocol violations without deleting evidence or
rewriting terminal run outcomes. Main-session review accepted the subagent
implementation.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Runtime resolution records and CLI | completed | codex | main |  | 2026-05-04 |
| 02 | Status/alerts overlay, docs, validation | completed | codex | main | 01 | 2026-05-04 |

## Activity Log

- 2026-05-04 codex: triaged GitHub issue #19 as valid but scoped out
  coordinator re-entry for this spec.
- 2026-05-04 codex: created the spec and prepared it for subagent
  implementation with main-session review.
- 2026-05-04 codex: implemented append-only protocol resolution records,
  Codex-facing CLI, status/alerts overlays, legacy `kind` normalization, and
  operator/heartbeat guidance.
- 2026-05-04 codex: validated focused status/control-surface tests, full
  unittest discovery, CLI help surfaces, and `git diff --check`.
- 2026-05-04 codex: main-session review accepted the implementation, reran
  validation, and verified a temporary end-to-end resolution fixture.

## Spec Handoff

- Spec path: `specs/rfc-0023-protocol-violation-resolution`
- Status: done
- Spec type: compact runtime/status bugfix
- Open questions: coordinator re-entry and resolution reversal are follow-ups
- Workstreams: `01-runtime-resolution`, `02-status-docs-validation`
- Next owner: none
- Validation expectation: focused status/CLI tests, full unittest discovery,
  CLI smoke, diff check, and read-only dogfood status/alerts check
- Ready to implement: complete
