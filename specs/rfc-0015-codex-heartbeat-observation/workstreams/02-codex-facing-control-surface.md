---
language: en-US
audience: agent
doc_type: workstream
status: validated
updated: 2026-05-02
---

# 02 - Codex-Facing Control Surface

## Scope

Added machine-readable runtime commands that interactive Codex can call
after a heartbeat wakeup or user status request:

- `status --json` `next_actions`
- `events --since` event delta reads
- `alerts --json` material alert reads
- `resolve-decision` decision resolution after user approval
- report-schema repair or compatibility actions if dogfood proves necessary

## Acceptance

1. Done: commands are non-interactive and JSON-first.
2. Done: status includes actionable next steps for Codex.
3. Done: decision resolution records the user's approved option in `.dispatch/`.
4. Done: tests cover pending decisions, protocol violations, event deltas,
   alerts, and decision option validation.

## Validation

- `PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface`
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- `python3 scripts/de.py events --help`
- `python3 scripts/de.py alerts --help`
- `python3 scripts/de.py resolve-decision --help`
