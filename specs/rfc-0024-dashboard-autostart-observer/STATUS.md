---
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: passed
updated: 2026-05-06
---

# Status

## Summary

The read-only Dispatch Engine dashboard observer and prototype-parity baseline
are locally committed at `a1565dd`. The dashboard now serves from the skill
root through `de dashboard`, opens as a Codex browser observer, and includes
overview, agents, plan/workstreams, decisions, capabilities, validators,
alerts, history, logs, theme/density preferences, command-preview modals,
state overlays, and event-tail filtering/collapse/resize. It remains
read-only: dashboard viewing and browser preferences must not mutate
`.dispatch/` runtime evidence.

Validation passed locally with focused dashboard tests, full unittest
discovery, JavaScript syntax checking, and whitespace checks. Browser visual
review found and fixed several responsive and prototype-parity defects. Remote
push/install sync remain follow-up project operations outside this spec
baseline.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Dashboard server lifecycle and API | validated | worker-01-server-api | main |  | 2026-05-05 |
| 02 | Static dashboard UI from prototype | validated | worker-02-static-ui | main | 01 | 2026-05-05 |
| 03 | Skill docs, tests, and browser validation | validated | worker-03-docs-autostart | main | 01, 02 | 2026-05-05 |
| 04 | Theme, density, settings, and keyboard shell | validated | worker-004-theme-settings-keyboard | main | 02 | 2026-05-05 |
| 05 | Agent roster drilldown and agent detail status view | validated | worker-005-agent-detail | main | 02, 04 | 2026-05-05 |
| 06 | Plan explorer, searchable tree, and coordinator log view | validated | worker-006-plan-explorer | main | 02, 04 | 2026-05-05 |
| 07 | Read-only command/status/tail/decision/capability modals | validated | worker-007-modals-command-previews | main | 02, 04, 05 | 2026-05-05 |
| 08 | Run switcher, history filter, and two-run comparison | validated | worker-008-history-run-switcher | main | 02, 04 | 2026-05-05 |
| 09 | Empty, terminal, disconnected, waiting-input, and violation states | validated | worker-009-state-overlays | main | 02, 04 | 2026-05-05 |
| 10 | Full prototype parity validation matrix | validated | worker-010-parity-validation | main | 04, 05, 06, 07, 08, 09 | 2026-05-05 |

## Activity Log

- 2026-05-05 codex: created spec from the user's request to autostart a
  dashboard service and open it in the Codex browser when DE is actively used.
- 2026-05-05 codex: completed the spec as a three-step subagent plan:
  server/API first, static UI second, docs/tests/browser validation third.
- 2026-05-05 worker-01-server-api: claimed Workstream 01 and began
  dashboard server lifecycle/API implementation.
- 2026-05-05 worker-01-server-api: completed and validated Workstream 01
  server/API scope with focused dashboard tests, CLI help, related regression
  tests, and `git diff --check`.
- 2026-05-05 worker-03-docs-autostart: documented dashboard autostart and
  Codex in-app browser guidance, clarified read-only scope, and validated with
  `python3 scripts/de.py dashboard --help` plus `git diff --check`.
- 2026-05-05 worker-02-static-ui: completed dependency-free dashboard assets
  and validated focused dashboard behavior.
- 2026-05-05 worker-04-dashboard-validation: added focused static asset
  serving coverage and validated focused dashboard tests, dashboard help, and
  diff check. Coordinator reran full unittest discovery successfully after the
  root help text changed to `Start or report on a local dashboard observer.`;
  browser visual evidence was not run in that worker because the coordinator
  owns that evidence.
- 2026-05-05 codex: verified the running dashboard at
  `http://127.0.0.1:57094/` with API/static smoke checks and browser evidence
  under `.out/screenshots/` plus `.playwright-mcp/` console/page snapshots.
- 2026-05-05 codex: reran
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`,
  `PYTHONPATH=scripts python3 -m unittest discover -s tests`,
  `python3 scripts/de.py dashboard --help`, and `git diff --check`; all passed.
- 2026-05-05 codex: cancelled dogfood run `20260505T083305787272Z` after main
  validation because `worker-04-dashboard-validation` did not produce a
  terminal report; filed https://github.com/wo1fsea/dispatch-engine/issues/20.
- 2026-05-05 codex: after user review, reclassified rfc-0024 from complete
  baseline to partial prototype parity. Added missing prototype scope for
  themes/density, keyboard controls, run switcher, plan search, clickable agent
  detail, modals, state overlays, and history compare.
- 2026-05-05 codex: recorded the data availability decision: full completion
  restores every prototype surface, while missing real runtime fields must stay
  visible as explicit empty/unavailable states or opt-in fixture states and be
  reported back in a final data parity report.
- 2026-05-05 codex: captured the local prototype into
  `specs/rfc-0024-dashboard-autostart-observer/prototype/` so future workers
  validate against repo-owned source files rather than a machine-local
  Downloads path.
- 2026-05-05 codex-workers: created planned workstream specs 04-10 for
  theme/settings/keyboard shell, agent detail, plan explorer, modal previews,
  run history, state overlays, and final parity validation.
- 2026-05-05 codex-worker: created
  `.dispatch/plans/rfc-0024-prototype-parity.json` for conservative serial
  Dispatch Engine execution of workstreams 04-10 while preserving the
  validated dashboard observer baseline.
- 2026-05-05 codex: tightened final acceptance to require strict
  prototype-design parity, including icon/ico/icon-only button audit, visual
  weight, spacing, tooltips, and hover/active/disabled states.
- 2026-05-05 worker-004-theme-settings-keyboard: claimed Workstream 04 and
  started dependency-free restoration of theme presets, density persistence,
  settings popover, topbar command modals, and keyboard shell shortcuts.
- 2026-05-05 worker-004-theme-settings-keyboard: validated Workstream 04 with
  `python3 scripts/de.py dashboard --help`,
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`, and
  `git diff --check`. Browser screenshot validation remains coordinator-owned
  for this run because this worker's capability profile disallows service
  starts beyond the listed command validation.
- 2026-05-05 worker-005-agent-detail: claimed, implemented, and validated
  Workstream 05. Agent roster cards now open a read-only agent detail screen
  backed by `/api/agent/<agent-id>`, with logs, report, file scope,
  heartbeat, metadata, capability, and command-preview empty states.
- 2026-05-05 worker-006-plan-explorer: claimed, implemented, and validated
  Workstream 06. The dashboard now exposes `/api/plan`, renders a searchable
  recursive plan tree with dependency metadata and selected/expanded row state,
  and shows coordinator stdout/stderr in a terminal-style panel with missing
  data empty states.
- 2026-05-05 worker-007-modals-command-previews: claimed, implemented, and
  validated Workstream 07. The dashboard now uses a shared read-only modal
  system for tail/status JSON, cancel preview, pending decisions, capability
  review, keyboard help, run selector, and agent-detail log/report/cancel/
  capability previews, with command previews and explicit unavailable states
  instead of browser-side mutation.
- 2026-05-05 worker-008-history-run-switcher: claimed, implemented, and
  validated Workstream 08. The dashboard now exposes richer read-only
  `/api/history` fields and restores recent-run navigation, the breadcrumb run
  switcher with safe command previews, searchable/exportable history, and
  two-run comparison deltas.
- 2026-05-05 worker-009-state-overlays: implemented and validated Workstream
  09. The dashboard now derives scenario overlays for empty, starting,
  running, waiting-input, violation-flash, disconnected, coordinator-dead,
  completed, cancelled, and failed states; terminal headers freeze clock
  treatment; banners route to retry/log/decision/review affordances; and
  opt-in query-string fixture mode is visibly labeled and browser-only.
- 2026-05-05 worker-010-parity-validation: claimed Workstream 10 and added
  the worker-side prototype parity matrix, data parity report, and icon audit
  to `PROTOTYPE_PARITY.md`. Browser screenshot and console evidence remain
  coordinator-owned for run `20260505T095306005146Z`.
- 2026-05-05 worker-010-parity-validation: validated Workstream 10 with
  `python3 scripts/de.py dashboard --help`,
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`,
  `PYTHONPATH=scripts python3 -m unittest discover -s tests`, and
  `git diff --check`; all passed.
- 2026-05-05 codex: tightened the host heartbeat dashboard contract after
  visual review. `Host heartbeat` now represents the outer interactive Codex
  heartbeat, reads a run-scoped `host-heartbeat.json` snapshot through a
  read-only dashboard API when available, shows an explicit missing state for
  active runs without that snapshot, and derives only terminal stopped
  treatment from run state to avoid stale countdowns.

## Spec Handoff

- Spec path: `specs/rfc-0024-dashboard-autostart-observer`
- Status: ready-review; local prototype-parity baseline validated
- Spec type: runtime/frontend feature
- Open questions: write actions and tokenized localhost access are follow-ups
- Prototype fixture:
  `specs/rfc-0024-dashboard-autostart-observer/prototype/`
- Dispatch plan: `.dispatch/plans/rfc-0024-prototype-parity.json`
- Workstreams: `01-server-api`, `02-static-ui`, `03-docs-tests-validation`,
  `04-theme-settings-keyboard`, `05-agent-detail`, `06-plan-explorer`,
  `07-modals-command-previews`, `08-history-run-switcher`,
  `09-state-overlays`, `10-parity-validation`
- Next owner: maintainer/operator for push, installed-skill sync, and the
  validator-role policy follow-up
- Validation expectation: continue using existing baseline checks plus browser
  visual review for future UI changes
- Completion report expectation: include a data parity report that lists every
  prototype surface, its real runtime data source or missing source, whether it
  is live/empty-state/fixture-only/blocked, and any Dispatch Engine API/runtime
  follow-up issues
- Ready to implement: completed locally; follow-ups should become separate
  specs/issues if they require runtime behavior changes

## 2026-05-06 Interactive Review Follow-up

- Event tail responsiveness has been tightened after visual review:
  collapse/expand stays inside the tail header on narrow viewports, collapsed
  state no longer reserves expanded blank height, and the expanded tail now
  supports dragging its top edge to resize.
- Tail height is stored only as a browser-local preference
  `dispatch-engine.dashboard.tailHeight`; no `.dispatch/` runtime evidence is
  mutated by dashboard viewing or resizing.
- Validators page semantics were clarified after review: it shows registered
  `role: "validator"` agents and role-specific validation evidence. The current
  dashboard dogfood run has no validator agents, so the empty Validators page
  is expected rather than a data-load failure.
- Local baseline committed as `a1565dd` after validation:
  `node --check dashboard/app.js`,
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`,
  `PYTHONPATH=scripts python3 -m unittest discover -s tests`, and
  `git diff --check`.
