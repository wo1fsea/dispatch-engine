---
spec_id: rfc-0006-live-coordinator-supervision
language: en-US
audience: agent
doc_type: spec
status: validated
implementation: validated
validation: validated
coordinator: dispatch-engine
updated: 2026-05-02
---

# Status

## Summary

Implementation is validated. This spec turns `de run` from dry-run-only rendering into foreground provider CLI coordinator supervision while preserving dry-run, default Codex provider selection, explicit Claude support, centralized prompt templates, and observable `.dispatch/` state.

Runtime validation evidence comes from Worker A's recorded full unittest and live-supervision test pass, plus coordinator review rerunning full unittest discovery, CLI help, and whitespace checks. Worker B validated the documentation/status baseline with the targeted docs search and whitespace diff check listed in workstream 02.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Live launch process supervision | validated | Worker A | main |  | 2026-05-02 |
| 02 | Event/status/docs validation | validated | Worker B | main | 01 | 2026-05-02 |

## Activity Log

- 2026-05-02 codex: created ready RFC for foreground live coordinator supervision after rfc-0005 dry-run baseline.
- 2026-05-02 Worker A: claimed workstream 01 and began live launch process supervision implementation.
- 2026-05-02 Worker A: validated workstream 01 implementation with fake-provider unit tests, full unittest discovery, CLI help, and `git diff --check`.
- 2026-05-02 Worker B: updated rfc-0006 docs/status to the live `de run` baseline and validated docs references plus whitespace diff.
- 2026-05-02 codex: reviewed Worker A and Worker B outputs, checked installed Codex and Claude CLI help, unified provider launch so Codex and Claude receive a short instruction pointing to the recorded coordinator prompt snapshot, reran full unittest discovery, CLI help/version, and whitespace checks, and marked rfc-0006 validated.
- 2026-05-02 codex: aligned with operator decision that both Codex and Claude should receive the instruction file path rather than inline coordinator prompt content; narrow provider tests and full unittest discovery passed.

## Spec Handoff

- Spec path: `specs/rfc-0006-live-coordinator-supervision`
- Status: validated
- Spec type: runtime/process supervision
- Open questions: none blocking
- Workstreams: `01-live-launch-process-supervision`, `02-event-status-docs-validation`
- Next owner: baseline committer
- Validation evidence: Worker A recorded fake-provider unit tests, full unittest discovery, CLI help, and `git diff --check`; Worker B ran docs search and `git diff --check`; coordinator review checked installed `codex exec --help` and `claude --help`, then reran `PYTHONPATH=scripts python3 -m unittest discover -s tests`, `python3 scripts/de.py --help`, `python3 scripts/de.py version`, and `git diff --check`.
- Ready to implement: complete and validated
