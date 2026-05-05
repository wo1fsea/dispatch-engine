---
workstream_id: "05"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-005-agent-detail
branch: main
depends_on:
  - "02"
  - "04"
claimed_at: 2026-05-05T17:53:06+08:00
lease_expires_at: 2026-05-05T19:53:06+08:00
updated: 2026-05-05
---

# Workstream 05: Agent Roster Drilldown And Agent Detail

## Scope

Restore prototype parity for clicking an agent card and opening the `agent`
detail screen. The detail view must cover coordinator, worker, reviewer, and
validator records with live Dispatch Engine data where available and explicit
empty states where the runtime does not expose a prototype field yet.

## Acceptance

- Agent roster cards match the prototype interaction model:
  - Coordinator, workers, reviewers, and validators render in one roster.
  - Each card shows role, id, status, task, capability profile/chips, heartbeat
    state, last heartbeat age, and file count.
  - Coordinator cards retain distinct visual treatment.
  - Cards are clickable and keyboard accessible.
  - Selecting a card switches to the `agent` detail screen and preserves the
    selected agent id until the user navigates away or presses back.
  - Missing agent data renders an explicit empty state instead of a blank card.
- Agent detail header matches the prototype:
  - Back button returns to the agents roster.
  - Header shows role, id, task, status, profile, spawned-by, workstream, and
    provider.
  - Status and profile pills use the same status palette as the roster.
  - The header remains readable for long agent ids and long task text.
- Agent detail toolbar is read-only:
  - Log button opens or focuses agent stdout/stderr tail.
  - Report button opens a report JSON/summary surface, or shows "No report yet"
    when no report exists.
  - Cancel-agent button opens a command-preview or unavailable-state modal; it
    does not terminate a process.
  - Capability review/escalation button opens the capability review modal from
    the detail screen when capability data exists, or an unavailable state when
    it does not.
- Recent logs section matches the prototype terminal treatment:
  - Shows recent stdout and stderr for the selected agent when available.
  - Displays log source paths such as
    `.dispatch/runs/<run-id>/logs/<agent-id>.stdout.log`.
  - Shows live-tail/tailing indicator when data is being refreshed.
  - Escapes raw log text safely; do not render agent log lines as trusted HTML.
  - Empty states include "No stdout recorded", "No stderr recorded", or
    equivalent specific text.
- File scope / writes-so-far section matches prototype intent:
  - Shows assigned file scope from the worker prompt/registration when
    available.
  - Shows changed files from worker/reviewer/validator report evidence when
    available, including new/modified/deleted tone and addition/deletion counts
    when the report supplies them.
  - Shows "No changed files recorded" when no report or write evidence exists.
- Heartbeat history matches the prototype:
  - Renders a mini-chart for recent heartbeat samples.
  - Distinguishes ok, late, and missed/unavailable heartbeat samples.
  - Shows counts and time range labels.
  - Shows "No heartbeat samples recorded" when heartbeat history is absent.
- Agent metadata panel matches the prototype:
  - Includes id, role, spawned-by, spawned-at, workstream, capability profile,
    permission scope, provider, prompt path, report path, and launch evidence
    when available.
  - Missing fields are shown as `unavailable`, `pending`, or equivalent
    explicit values.
- Capability grant panel matches the prototype:
  - Shows granted capabilities, high-risk markers, exercised capabilities, and
    escalation state.
  - Links to the capability review modal from the detail screen.
  - Shows "No capability grant recorded" or "No exercised capabilities
    recorded" when runtime state lacks those fields.
- All live-mode data comes from real dashboard API or `.dispatch/`-backed
  server adapters. Prototype mock agent data may appear only in an opt-in,
  visibly marked fixture/demo mode.

## Implementation Notes

- Use `prototype/components.jsx` agent roster and `prototype/screens.jsx`
  `AgentDetail` as the visual and interaction source of truth.
- Prefer adding structured read-only server adapters over parsing `.dispatch/`
  files in browser JavaScript. Expected future endpoints include:
  - `GET /api/agent/<agent-id>`
  - `GET /api/logs/agent/<agent-id>`
  - `GET /api/report/<agent-id>`
- Until those endpoints exist, derive the roster from `/api/status`,
  `/api/events`, `/api/alerts`, `/api/tail`, and existing agent records, then
  render unavailable states for fields not exposed.
- Candidate data sources:
  - `.dispatch/runs/<run-id>/agents/` for registration and heartbeat records.
  - `.dispatch/runs/<run-id>/prompts/<agent-id>.md` for prompt path and
    assigned scope, when exposed by the server.
  - `.dispatch/runs/<run-id>/reports/<agent-id>.json` for changed files,
    report status, exercised capabilities, and validation details.
  - `.dispatch/runs/<run-id>/reviews/<agent-id>.json` and
    `.dispatch/runs/<run-id>/validation/<agent-id>.json` for reviewer and
    validator-specific evidence.
  - `.dispatch/runs/<run-id>/logs/<agent-id>.stdout.log` and `.stderr.log` for
    log panels.
  - event/tail records for heartbeat, spawn, completion, violation, and
    capability events.
- Preserve read-only semantics. Buttons may reveal paths, JSON, or command
  previews; they must not execute commands or mutate run state.
- Keep the selected agent screen URL/hash-friendly if the surrounding app uses
  URL state, but do not require a server restart or additional dashboard
  process per agent.

## Validation

Run baseline checks:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
python3 scripts/de.py dashboard --help
git diff --check
```

Browser validation:

- Open the agents screen and click at least one coordinator, worker, reviewer,
  and validator card.
- Verify each click opens the agent detail screen with the correct selected id.
- Use the back button and keyboard navigation to return to the roster.
- Verify logs, report, cancel preview, and capability review controls open
  read-only surfaces or explicit unavailable states.
- Validate an agent with no report, no changed files, and no heartbeat samples
  renders nonblank empty states.
- Check long ids/tasks, desktop/mobile widths, all themes, and all zoom levels
  for overlap.
- Check browser console output for uncaught errors.

## Activity Log

- 2026-05-05 codex-worker: created Workstream 05 parity spec for clickable
  agent roster drilldown and prototype-complete agent detail restoration.
- 2026-05-05 worker-005-agent-detail: claimed Workstream 05 for run
  `20260505T095306005146Z`.
- 2026-05-05 worker-005-agent-detail: implemented and validated the read-only
  agent detail API and dashboard screen, including clickable cards, back
  navigation, logs/report/cancel/capability previews, file scope, heartbeat
  history, metadata, capability grants, and explicit empty states.
