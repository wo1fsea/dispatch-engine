---
spec_id: rfc-0007-worker-adapter-protocol
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

Implementation is validated. This spec defines the worker adapter protocol needed after live coordinator supervision: registered worker identity, scoped workstream assignment, centralized worker prompts, durable worker reports, status visibility, and conservative protocol violations.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Worker state/report protocol | validated | codex | main |  | 2026-05-02 |
| 02 | Worker prompt template | validated | codex | main | 01 | 2026-05-02 |
| 03 | Status and protocol violations | validated | codex | main | 01 | 2026-05-02 |
| 04 | Docs and validation | validated | codex | main | 01, 02, 03 | 2026-05-02 |

## Activity Log

- 2026-05-02 codex: created ready RFC after rfc-0006 established foreground provider CLI coordinator supervision.
- 2026-05-02 codex: implemented workstream 01 helper-first worker registration/report protocol, added focused tests, and updated status violation detection to require valid implementation-agent reports.
- 2026-05-02 codex: validated with `PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol`, full unittest discovery, CLI help/version, and `git diff --check`.
- 2026-05-02 codex: implemented centralized worker prompt rendering from `references/prompts/worker-protocol.md`, added prompt contract tests, added protocol violation event coverage, and updated worker/event/operator docs for the helper-first rfc-0007 baseline.
- 2026-05-02 codex: validated rfc-0007 with focused worker adapter tests, full unittest discovery, CLI help/version smoke checks, documentation `rg`, and `git diff --check`.
- 2026-05-02 codex: review found worker prompt rendering did not yet write prompt snapshots; added `write_worker_prompt_snapshot`, prompt snapshot test coverage, and reran validation.
- 2026-05-02 codex: review hardened allowed write root matching so `src` does not match sibling prefixes such as `srcology`, then reran focused and full validation.

## Spec Handoff

- Spec path: `specs/rfc-0007-worker-adapter-protocol`
- Status: validated
- Spec type: runtime/worker protocol
- Open questions: generated vs caller-provided worker ids; exact/prefix/glob scope semantics; future real worker provider launch remains out of scope for this helper-first MVP
- Workstreams: `01-worker-state-report-protocol`, `02-worker-prompt-template`, `03-status-violations`, `04-docs-validation`
- Next owner: baseline committer
- Validation evidence: `PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol`; `PYTHONPATH=scripts python3 -m unittest discover -s tests`; `python3 scripts/de.py --help`; `python3 scripts/de.py version`; `rg "worker|worker-protocol|agent.spawned|workstream.assigned|protocol.violation|reports/" README.md SKILL.md references specs/rfc-0007-worker-adapter-protocol`; `git diff --check`
- Ready to review: complete and validated; no scheduler or real worker provider launch was added.
