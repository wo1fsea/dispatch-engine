---
workstream_id: "08"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-008-history-run-switcher
depends_on: ["02", "04"]
updated: 2026-05-05
---

# Workstream 08: Run History And Run Switcher

## Scope

Restore the prototype run navigation and history comparison surfaces from
`prototype/modals.jsx`, `prototype/scenarios.jsx`, `prototype/screens.jsx`,
`prototype/components.jsx`, and the root prototype wiring.

This workstream owns:

- Sidebar recent runs list with status dots, short run ids, current-run
  treatment, and empty history state.
- Breadcrumb run switcher popover listing active/recent runs, current run
  active state, repo/plan/status/elapsed/workers metadata, and a pick action.
- Safe run selection semantics for the current read-only server model.
- History screen table with run id, repo, plan/objective, started time,
  duration, workers, decisions, outcome, and terminal reason when available.
- History filter/search across run id, repo, plan/objective, status, and
  decision/worker counts.
- Client-side CSV export from already-loaded read-only history data.
- Two-run selection and comparison drawer showing duration, workers,
  decisions, files changed, tests, status, outcome, and deltas.

## Acceptance

- `/api/history` remains the canonical history source for live mode. The UI
  does not scan `.dispatch/` directly from browser JavaScript.
- The sidebar recent-runs list renders the newest available runs and preserves
  the prototype's compact visual treatment. If `/api/history` returns no runs,
  the list remains visible with an explicit empty state.
- The breadcrumb run tag opens a popover equivalent to the prototype
  `RunSwitcher`: anchored to the breadcrumb, current run highlighted, outside
  click and `Escape` close, and no layout jump.
- Picking the current run is a no-op with visible active state.
- Picking a different run uses the safest supported behavior:
  - if the current dashboard server supports `?run_id=<id>` or equivalent
    read-only context switching, update the URL/context without mutating state;
  - otherwise show a command/open preview explaining how to start or reuse that
    run's dashboard with `de dashboard <repo> --run-id <id> --detach --json`.
- The history screen includes a visible filter/search input, clear control, row
  count, and empty-no-results state.
- Filtering is case-insensitive and covers run id, repo, plan/objective,
  status, and terminal reason.
- CSV export uses the loaded history rows only, includes stable headers, and
  does not make extra mutating requests.
- Two-run comparison supports selecting exactly two rows, replacing the oldest
  selected row when a third is chosen or clearly disabling third selection.
- Comparison drawer shows both selected runs side by side and computes deltas
  for duration, workers, decisions, files changed, and tests when numeric data
  exists.
- Missing comparison fields render `unavailable` or `not exposed` in the drawer
  instead of disappearing.
- Completed, failed, cancelled, running, waiting-input, and unknown statuses
  get distinct status dots/pills matching the prototype tone.
- Desktop and mobile layouts preserve readable history rows and comparison
  drawer controls without overlap.

## Implementation Notes

- Extend `_run_history()` only with read-only fields that can be derived from
  existing run evidence: `run.json`, events, decisions, reports, validation
  reports, and dashboard metadata.
- Prefer adding structured history fields server-side over parsing free-form
  strings client-side. Candidate fields:
  - `run_id`, `short_id`, `repo`, `plan_id`, `objective`, `status`;
  - `created_at`, `started_at`, `updated_at`, `completed_at`, `duration_ms`;
  - `worker_count`, `agent_count`, `decision_count`,
    `pending_decision_count`;
  - `files_changed_count`, `tests_passed`, `tests_total`, `terminal_reason`;
  - `dashboard_url` or `dashboard_command_preview` when available.
- When a field is not yet exposed, keep the table column and comparison row
  visible with `not exposed`; Workstream 10 must capture it in the data parity
  report.
- Keep active-run switching read-only. Do not add server-side writes or
  dashboard metadata mutations just to mark a selected run.
- Use fixture mode only for parity examples that cannot be produced from local
  `.dispatch/` history, and label fixture rows clearly.

## Validation

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py dashboard --help
git diff --check
```

Focused validation:

- Unit-test `/api/history` for stable fields, empty-history behavior, and
  non-mutating reads.
- Browser-test run switcher open, close, current-run no-op, and different-run
  command/open preview.
- Browser-test history filter with matching and no-result queries.
- Browser-test CSV export content for the currently loaded rows.
- Browser-test selecting two runs and verifying comparison drawer deltas and
  unavailable-field rendering.
- Capture desktop and mobile screenshots for the switcher, filtered history,
  and comparison drawer.
- Verify browser console remains error-free during switcher/history flows.

## Activity Log

- 2026-05-05 codex-worker: created planned Workstream 08 spec for run
  switcher, history filtering, export, and two-run comparison parity.
- 2026-05-05 worker-008-history-run-switcher: claimed, implemented, and
  validated Workstream 08. `/api/history` now returns stable derived run
  fields from read-only evidence, and the dependency-free dashboard restores
  sidebar recent runs, breadcrumb run switcher, current-run no-op treatment,
  different-run command previews, history search/filter, client-side CSV
  export, two-run selection, and comparison deltas. Browser screenshot
  evidence remains coordinator-owned because this worker's capability profile
  allows only the listed command validation and no service starts.
