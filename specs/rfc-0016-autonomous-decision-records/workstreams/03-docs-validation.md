---
spec_id: rfc-0016-autonomous-decision-records
workstream_id: "03"
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker B
updated: 2026-05-03
---

# Docs And Validation

## Scope

Update the skill and reference docs to describe the autonomous record format and
the boundary between outer Codex judgment and runtime persistence.

## Files

- `SKILL.md`
- `README.md`
- `references/heartbeat-observation.md`
- `references/decision-blocker-protocol.md`
- `references/operator-flow.md`
- `references/operator-guide.md`
- `specs/README.md`
- `specs/rfc-0016-autonomous-decision-records/STATUS.md`

## Requirements

- Document the CLI flags and status summary.
- State that outer Codex/heartbeat owns eligibility judgment.
- State that runtime validates durable metadata only.
- Mark validation commands when implementation passes.

## Activity Log

- 2026-05-03: Worker B claimed docs/guidance workstream and began updating
  skill/reference guidance for RFC-0016.
- 2026-05-03: Updated owned skill, README, operator, heartbeat, and
  decision/blocker docs for structured autonomous technical decision records.
  Ran docs/CLI smoke checks, `tests.test_autonomous_decision_records`, and
  `git diff --check`; full RFC validation remains pending on runtime/status
  workstream evidence.

## Validation

```bash
rg "autonomous_technical|autonomous_decisions|autonomous-technical|interactive-codex-autonomous" SKILL.md README.md references specs/rfc-0016-autonomous-decision-records
git diff --check
```
