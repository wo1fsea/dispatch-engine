---
workstream_id: "06"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-006-plan-explorer
branch: main
depends_on:
  - "02"
  - "04"
claimed_at: 2026-05-05T09:53:06+00:00
lease_expires_at: 2026-05-05T11:53:06+00:00
updated: 2026-05-05
---

# Workstream 06: Plan Explorer, Searchable Tree, And Coordinator Log

## Scope

Restore prototype parity for the plan screen: searchable recursive plan tree,
selected/highlighted workstream rows, coordinator stdout/stderr terminal tail,
and mapping between plan/workstream status, events, and tail output.

## Acceptance

- Plan screen matches the prototype layout:
  - Main plan screen contains a searchable plan tree panel and a coordinator
    log panel.
  - The surrounding shell keeps the bottom event stream visible when the
    prototype keeps it visible.
  - Desktop and mobile layouts preserve information hierarchy without
    overlapping the tree, search field, footer, or terminal log.
- Plan tree is built from real run data:
  - Prefer `GET /api/plan` when available.
  - Until a dedicated endpoint exists, derive the tree from imported plan
    metadata, `workstream.planned` events, `/api/status` workstream
    assignments, and `/api/events` or `/api/tail`.
  - Root label reflects the imported plan id or plan file name when known.
  - Nodes represent phases, workstreams, dependencies, or available plan
    structure without hard-coded prototype mock names in live mode.
  - Missing plan data renders a visible "No plan tree available" state with
    the reason when known.
- Recursive tree behavior matches the prototype:
  - Parent nodes expand/collapse on click.
  - Leaf rows select/highlight on click.
  - Selected rows retain styling while the user filters or updates data.
  - Status dots map to normalized states: completed/ok, running, blocked/warn,
    queued/muted, failed/danger, and unknown.
  - Nested children are indented consistently and remain keyboard/screen-reader
    navigable.
- Search/filter behavior matches the prototype:
  - Search input is in the plan tree header with a search icon.
  - `/` focuses the search field when the plan screen is active.
  - Filtering matches node names case-insensitively; valid regex support may be
    added, but invalid regex input must not crash the dashboard.
  - Matching nodes remain visible with their ancestor path.
  - Matched labels receive hit/highlight styling.
  - Clear control resets the filter.
  - Footer shows either `click rows to expand · / to filter` or the active
    filter text.
- Coordinator log panel matches the prototype:
  - Shows coordinator stdout and stderr, either as tabs, split panels, or a
    combined terminal section with source labels.
  - Uses terminal-style rows with timestamp, severity/prefix, message, and
    caret/live-tail affordance.
  - Shows source paths such as
    `.dispatch/runs/<run-id>/logs/coordinator-001.stdout.log`.
  - Shows a live-tail indicator when the polling loop is refreshing.
  - Shows explicit empty states for missing stdout, missing stderr, or missing
    coordinator logs.
  - Escapes raw log text safely; do not render coordinator logs as trusted
    HTML.
- Event and tail mapping is explicit:
  - `/api/events?since=<cursor>` and `/api/tail` are normalized into a common
    client model for plan progress and the bottom event stream.
  - Workstream events update corresponding plan node status, progress,
    assignee, blocked reason, and selected row metadata when present.
  - Coordinator lifecycle, heartbeat, decision, capability, validation, and
    protocol-violation events map to readable event stream rows.
  - Invalid event cursors surface a visible API error and do not blank the plan
    screen.
  - Terminal/disconnected states pause or mark tail data stale without losing
    the last known plan tree.
- The implementation remains read-only. Plan tree, event, tail, and log
  controls never mutate `.dispatch/` state.

## Implementation Notes

- Use `prototype/screens.jsx` `PlanTreePanel` and `CoordLogPanel`,
  `prototype/scenarios.jsx` `PlanTreeWithSearch`, `prototype/data.js`
  `PLAN_TREE`, and the plan/log sections of `prototype/styles.css` as the
  source of truth.
- Prefer adding a structured read-only `GET /api/plan` server adapter over
  reconstructing plan topology entirely in browser JavaScript.
- The adapter should normalize:
  - imported plan id and source path;
  - workstreams, titles, statuses, dependencies, assignees, file counts, and
    blocked reasons;
  - phase/grouping information when present;
  - selected run metadata needed for headers and footer hints.
- Keep client event normalization centralized so overview workstream rows,
  plan tree status dots, event stream rows, and coordinator log affordances do
  not implement conflicting status mappings.
- Treat `/api/tail` as the latest durable event tail, not a write channel.
  Polling or manual refresh is acceptable for this workstream; SSE can remain a
  follow-up.
- Preserve existing baseline `/api/logs/coordinator` support and extend it only
  with additional metadata needed for parity, such as stdout/stderr paths,
  missing-file flags, and refresh timestamps.
- Fixture/demo mode may be used for parity validation of a rich plan tree, but
  it must be opt-in, visibly marked, and excluded from production live-mode
  data.

## Validation

Run baseline checks:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
python3 scripts/de.py dashboard --help
git diff --check
```

Additional focused validation should cover:

- Plan endpoint or adapter output for a run with imported plan metadata.
- Missing plan data rendering a nonblank empty state.
- Invalid event cursor handling without blanking the screen.
- Coordinator stdout/stderr payloads, including missing log files.

Browser validation:

- Open the plan screen and verify the recursive tree renders from live or
  fixture data.
- Expand/collapse multiple parent nodes and select leaf workstreams.
- Search for a workstream, clear the search, and verify footer hints update.
- Press `/` on the plan screen and verify search focus.
- Verify coordinator stdout/stderr terminal rows, live-tail indicator, source
  paths, caret, and empty states.
- Verify event stream rows and plan node statuses update after refresh/poll.
- Check desktop/mobile widths, all themes, and all zoom levels for overlap.
- Check browser console output for uncaught errors.

## Activity Log

- 2026-05-05 codex-worker: created Workstream 06 parity spec for searchable
  plan explorer, coordinator log, and event/tail mapping restoration.
- 2026-05-05 worker-006-plan-explorer: claimed Workstream 06 and started
  plan explorer/API restoration.
- 2026-05-05 worker-006-plan-explorer: implemented and validated the
  structured `/api/plan` adapter, searchable recursive plan tree, coordinator
  stdout/stderr terminal panel, and explicit missing plan/log empty states with
  `python3 scripts/de.py dashboard --help`,
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`, and
  `git diff --check`.
