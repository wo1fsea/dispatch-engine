---
language: en-US
audience: agent
doc_type: workstream
status: documented
updated: 2026-05-02
---

# 03 - Host Heartbeat Runbook

## Scope

Documented how interactive Codex should create or suggest a thread heartbeat
monitor after starting a detached run in hosts that support wakeups.

The runbook now lives at `references/heartbeat-observation.md` and is linked
from `SKILL.md`, `README.md`, `references/operator-flow.md`, and
`references/operator-guide.md`.

The runbook includes:

- when to create a heartbeat
- recommended interval guidance
- heartbeat prompt shape
- material-change reporting rules
- fallback wording when host wakeups are unavailable
- control-surface order: `status --json`, `events --since`, `alerts --json`,
  and `resolve-decision` after user approval

## Acceptance

1. Done: operator docs distinguish DE runtime state from host wakeup mechanics.
2. Done: the heartbeat prompt only describes the task; schedule/thread metadata
   stays in the host automation configuration.
3. Done: the runbook says to report decisions, blockers, failures, completed
   workstreams, and validation evidence, not unchanged activity.

## Validation

- `python3 scripts/de.py --help`
- `git diff --check`
- `rg "heartbeat|status --json|events --since|alerts --json|resolve-decision" SKILL.md README.md references specs/rfc-0015-codex-heartbeat-observation`
