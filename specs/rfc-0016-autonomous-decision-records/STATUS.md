---
spec_id: rfc-0016-autonomous-decision-records
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: completed
validation: passed
coordinator: dispatch-engine
updated: 2026-05-03
---

# Status

## Summary

Ready. This spec defines structured `.dispatch/` records for autonomous
technical decisions made by outer Codex after four unanswered heartbeat checks.
The goal is to make those choices auditable and easy to report without moving
choice-making logic into the Dispatch Engine runtime.

Runtime now supports `resolve-decision --autonomous-technical`, validates
structured metadata, stores source-of-truth records in `decisions.jsonl`, and
surfaces compact `status --json` `autonomous_decisions` summaries for heartbeat
and final-report use. Skill and reference guidance record that outer Codex owns
eligibility judgment while runtime owns durable persistence and mechanical
validation.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Runtime schema and CLI | validated | Worker A | main | rfc-0015 | 2026-05-03 |
| 02 | Status summary and tests | validated | Worker A | main | 01 | 2026-05-03 |
| 03 | Skill and reference docs | validated | Worker B | main | 01, 02 | 2026-05-03 |
| 04 | Review and validation | validated | codex | main | 01, 02, 03 | 2026-05-03 |

## Validation

- `PYTHONPATH=scripts python3 -m unittest tests.test_autonomous_decision_records`
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- `python3 scripts/de.py resolve-decision --help`
- `python3 scripts/de.py status --help`
- `rg "autonomous_technical|autonomous_decisions|autonomous-technical|interactive-codex-autonomous" SKILL.md README.md references specs/rfc-0016-autonomous-decision-records`
- `git diff --check`
