---
workstream_id: 02-status-and-decision-surfacing
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: agent
doc_type: workstream
status: planned
owner: unassigned
updated: 2026-05-03
depends_on:
  - 01-capability-contract
  - rfc-0011
  - rfc-0016
---

# Status And Decision Surfacing

## Scope

Make capability profiles visible through Dispatch Engine status, events,
decisions, blockers, alerts, and final-report summaries. This workstream turns
the profile contract into an operator-facing audit trail.

## Tasks

- Add `status --json` capability profile summaries for active agents.
- Surface high-risk grants such as network access, package installation, Docker
  socket use, service startup, unrestricted tests, runtime state writes, and
  GitHub issue creation.
- Surface pending capability escalation decisions and unresolved capability
  blockers.
- Emit events for profile grants, escalation requests, escalation resolutions,
  and capability violations.
- Link approved profile expansions to decision ids.
- Extend alert logic so capability violations and unresolved escalations appear
  in material alerts.
- Ensure final summaries can list grants, exercised capabilities, approved
  escalations, denied escalations, and violations.
- Keep autonomous technical-decision fallback bounded by RFC-0016 eligibility
  and exclusion rules.

## Acceptance

- `status --json` includes a `capability_profiles` object with active agents,
  pending decisions, and violations.
- `alerts --json` includes capability overreach and unresolved capability
  escalation blockers.
- Event logs include capability grant, escalation request, escalation
  resolution, and violation events.
- Decision records can approve or deny capability expansion without losing the
  original granted profile history.
- Status output remains compact enough for heartbeat consumption.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest tests.test_decision_blocker_protocol
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
python3 scripts/de.py events --help
git diff --check
```
