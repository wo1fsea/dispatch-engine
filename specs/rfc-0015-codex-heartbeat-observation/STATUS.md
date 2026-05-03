---
spec_id: rfc-0015-codex-heartbeat-observation
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

Ready. This spec records the corrected observation architecture: detached
Dispatch Engine runs remain visible through durable `.dispatch/` state, while
foreground Codex can only explain background progress after a user message or a
host-provided thread heartbeat wakes it.

The spec and guidance baseline is complete. The host heartbeat runbook is
documented in `references/heartbeat-observation.md` and linked from the skill,
README, and operator docs. Runtime now exposes the Codex-facing control
surfaces: `status --json` `next_actions`, `events --since`, `alerts --json`,
and `resolve-decision`. The heartbeat policy has been tightened: heartbeat
observation is required after every interactive detached launch when the host
supports wakeups, and the heartbeat must be stopped once the run reaches a
terminal state. The default heartbeat interval is 15 minutes.
After four consecutive heartbeat checks with the same pending technical
decision unresolved, outer Codex may make a conservative autonomous technical
choice, record it with actor `interactive-codex-autonomous`, continue the run,
and report all such choices at completion.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Spec and guidance baseline | validated | codex | main | rfc-0014 | 2026-05-02 |
| 02 | Codex-facing control surface | validated | codex | main | 01 | 2026-05-02 |
| 03 | Host heartbeat runbook | validated | codex | main | 01 | 2026-05-03 |
| 04 | Validation and dogfood | validated | codex | main | 02, 03 | 2026-05-02 |

## Validation

- `PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface`
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- `python3 scripts/de.py events --help`
- `python3 scripts/de.py alerts --help`
- `python3 scripts/de.py resolve-decision --help`
- `python3 scripts/de.py --help`
- `python3 scripts/de.py status --help`
- Temporary target smoke: import fixture plan, then read `status --json`,
  `events --since event-000001 --json`, and `alerts --json`
- `git diff --check`
- `rg "heartbeat|status --json|events --since|alerts --json|resolve-decision" SKILL.md README.md references specs/rfc-0015-codex-heartbeat-observation`
