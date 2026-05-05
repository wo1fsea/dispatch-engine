---
language: en-US
audience: agent
doc_type: spec
---

# Prototype Parity Requirement

This spec requires a **one-to-one functional and visual restoration** of the
repo-captured prototype fixture at:

```text
specs/rfc-0024-dashboard-autostart-observer/prototype/
```

The fixture was captured from
`/Users/huangquanyong/Downloads/dispatch engine dashboard` on 2026-05-05 so
Dispatch Engine workers can validate parity without relying on a machine-local
Downloads path.

The current dashboard baseline is not sufficient. Implementers must treat the
prototype as the source of truth for layout, visual density, interaction model,
screen coverage, component behavior, state treatment, icons, and operator
affordances. The production dashboard may replace mock data with real
`.dispatch/` state, empty states, or read-only command previews, but it must
not silently omit a prototype feature.

## Source Inventory

The prototype consists of:

- `Dispatch Engine Dashboard.html`: root application, routing, keyboard
  shortcuts, tweak defaults, run switcher, modal wiring, scenario wiring.
- `styles.css`: base layout, shell, panels, typography, nav, event stream,
  timeline, heartbeats, tables, agent detail, history, modals, scenario
  overlays, empty state, responsive layout.
- `themes.css`: theme presets.
- `data.js`: mock domain model for run, workstreams, agents, decisions,
  alerts, history, validators, plan tree, event templates, coordinator logs.
- `components.jsx`: topbar, settings popover, sidebar, event stream, run
  header, workstream list, heartbeat card, decisions list, alerts list, agent
  roster, command modal, status helpers.
- `screens.jsx`: plan tree panel, capability table, validator panel,
  coordinator log panel, run history panel, agent detail screen.
- `modals.jsx`: modal shell, cancel run modal, decision modal, capability
  modal, keyboard help modal, run switcher.
- `scenarios.jsx`: scenario catalog, scenario run header, scenario overlays,
  empty dashboard, searchable plan tree, run history compare.
- `tweaks-panel.jsx`: host edit-mode protocol and reusable tweak controls.
- `scratch/01-running.png`, `scratch/02-empty.png`, `scratch/zoom.png`:
  visual references.

## One-to-one Rules

1. Every named screen, component, modal, scenario, keyboard shortcut, theme, and
   control in the prototype must have an equivalent in the bundled static
   dashboard.
2. Static implementation may be plain HTML/CSS/JS, but behavior must match the
   prototype. Do not drop interactions because the original uses React.
3. Mock data must be replaced with real dashboard API data when available.
   Missing runtime fields must render explicit empty or unavailable states,
   not disappear.
4. All write-like actions remain read-only in this release. They must open the
   same modal/control surface and show a command preview or chat-mediated next
   step.
5. Theme, density, keyboard, modal, agent-detail, history-compare, and scenario
   surfaces are part of the acceptance criteria, not optional polish.
6. Desktop and mobile layouts must preserve the prototype information
   hierarchy without incoherent overlap.
7. Icon parity is mandatory. Every icon, icon-only button, status mark, SVG
   path, favicon/ico asset when present, visual weight, hit target, tooltip,
   active/hover/disabled treatment, and spacing around icons must be checked
   against the prototype fixture. Do not replace prototype iconography with a
   generic icon set unless the resulting shape, size, stroke weight, semantics,
   and placement match the prototype during review.

## Data Availability Decision

One-to-one restoration means **prototype interaction and visual parity**, not
inventing fake production facts. Current Dispatch Engine run state does not yet
expose every field used by the prototype mock model. The implementation must
therefore use this rule:

- If real `.dispatch/` data exists, render it.
- If a runtime field is missing but the prototype has a corresponding surface,
  keep the surface visible and render an explicit empty/unavailable state.
- If parity validation needs rich examples that real data cannot provide yet,
  use a clearly separated fixture/demo mode. Fixture mode must be opt-in,
  visibly marked, and must not pollute production `.dispatch/` state.
- Do not silently remove prototype sections, buttons, charts, modals, or
  screens just because the current runtime lacks data.
- Do not hard-code prototype mock data into production live mode.

The final implementation report must include a **data parity report** with:

- every prototype data field or surface;
- the current production source, such as `/api/status`, `/api/history`,
  `/api/events`, agent records, reports, logs, or "not yet exposed";
- whether the surface is live, empty-state backed, fixture-only, or blocked;
- follow-up runtime/API gaps that should become issues or specs.

The dashboard can be accepted only when every prototype surface is either live
against real data or intentionally represented with a reviewed empty/fixture
state and listed in the data parity report.

## Required App Shell

- Sidebar with Dispatch Engine brand, current/no-active-run section, screen
  navigation, dynamic badges, and recent runs.
- Topbar with breadcrumbs, run selector, elapsed/state clock, tail-log button,
  status JSON button, settings button, cancel button when applicable.
- Main content area with scrollable screen content plus bottom event stream.
- Empty-mode shell for no active run.
- Active-run shell with scenario-specific class and screen label.
- Responsive mobile shell matching the prototype's vertical stacking behavior.

## Required Navigation

Screens:

- `overview`
- `agents`
- `plan`
- `decisions`
- `capabilities`
- `validators`
- `alerts`
- `history`
- `agent` detail

Keyboard shortcuts:

- `?`: keyboard help modal.
- `Escape`: close modal/popover or clear navigation chord.
- `x`: cancel preview modal.
- `c`: tail command modal.
- `s`: status JSON modal.
- `g o`: overview.
- `g a`: agents.
- `g p`: plan.
- `g d`: decisions.
- `g c`: capabilities.
- `g v`: validators.
- `g h`: history.

Keyboard handling must ignore text inputs and textareas.

Workstream 04 keyboard note: the bundled static dashboard implements these
shell shortcuts, ignores `input`, `textarea`, `select`, and contenteditable
targets, and also supports `g l` for the retained logs screen.

## Required Themes And Density

Themes:

- `default` / Mission cyan.
- `solar`.
- `carbon`.
- `indigo`.
- `forest`.
- `crimson`.

Controls:

- Settings popover anchored to topbar settings button.
- Theme swatches with active state and check mark.
- Density/zoom controls for `70%`, `80%`, `90%`, and `100%`.
- Preferences persisted in browser local storage.
- Theme and density apply instantly.

Workstream 04 status: implemented in the bundled dependency-free dashboard.
The static shell exposes the six prototype themes, a settings popover,
persisted density buttons, topbar tail/status/cancel/keyboard surfaces, and
read-only modal previews without writing `.dispatch/` state.

## Required Scenario States

The prototype scenario catalog must be represented:

- `empty`
- `starting`
- `running`
- `waiting-input`
- `violation-flash`
- `disconnected`
- `coordinator-dead`
- `completed`
- `cancelled`
- `failed`

Each state must have matching visual treatment:

- Scenario-aware run header label, subtitle, progress bar, stats, tags, and
  clock behavior.
- Empty dashboard with recent runs, plans, CTA buttons, and CLI preview.
- Violation toast with review affordance.
- Disconnected banner with retry/show-known affordances.
- Terminal states with frozen elapsed/clock behavior.

## Required Overview

- Scenario run header.
- Workstream timeline list.
- Heartbeat ring/card.
- Decisions list.
- Alerts list.
- Agent roster.
- Event stream.

## Required Workstreams And Plan

- Workstream list with progress, assignee, status, file count, and blocked
  reason.
- Plan tree with recursive expand/collapse.
- Search/filter input with clear control and footer hint.
- Status dots and selected/highlighted rows.
- Coordinator stdout/stderr panel with terminal-style log lines and live-tail
  indicator.

Workstream 06 status: implemented in the bundled dependency-free dashboard.
The plan screen now reads `GET /api/plan`, renders a recursive searchable
plan/workstream tree from imported run state and live assignment summaries,
preserves selected and expanded rows, highlights filter hits, shows dependency,
file, and validation metadata, and keeps explicit empty states for missing plan
or log data. The coordinator log panel uses `/api/logs/coordinator` stdout and
stderr text as escaped terminal rows with source paths and a cached/live-tail
indicator.

Workstream 09 status: implemented in the bundled dependency-free dashboard.
The shell now uses a browser-side scenario adapter for `empty`, `starting`,
`running`, `waiting-input`, `violation-flash`, `disconnected`,
`coordinator-dead`, `completed`, `cancelled`, and `failed`. Live mode derives
those states from `/api/status`, `/api/alerts`, fetch health, supervisor and
lifecycle diagnostics, pending decisions, and terminal fields. Rare-state
fixture mode is opt-in with `?fixture=<scenario>`, visibly labeled, and uses
browser-only demo data so `.dispatch/` evidence is not written.

## Required Agent Roster And Agent Detail

Agent roster:

- Coordinator, workers, reviewers, and validators.
- Role, status, task, profile, capability chips, heartbeat state, last
  heartbeat, file count.
- Clickable agent cards.

Clicking any agent must open the `agent` detail screen. Agent detail must show:

- Back button.
- Agent role, id, task, status, profile, spawned-by, workstream, provider.
- Toolbar buttons for logs, report, and cancel-agent preview.
- Recent stdout/stderr terminal panel.
- File scope / writes-so-far list.
- Heartbeat history mini-chart.
- Agent metadata key/value panel.
- Capability grant panel with grants, exercised capabilities, and escalation
  state.
- Capability review modal can be opened from the detail screen.

Workstream 05 status: implemented in the bundled dependency-free dashboard.
Roster cards are clickable and keyboard accessible, switch to a read-only
agent detail screen, and fetch structured `.dispatch/`-backed data from
`/api/agent/<agent-id>`. The detail screen exposes back navigation, metadata,
stdout/stderr, report JSON or "No report yet", cancel-agent and capability
review previews, file scope, changed files, heartbeat history, capability
grants, exercised capability evidence, and explicit empty states for missing
runtime fields.

When real `.dispatch/` data does not include mock fields, render explicit
empty states such as "No report yet", "No changed files recorded", or "No
heartbeat samples recorded".

## Required Decisions

- Decisions list with id, question, source agent, since/heartbeat age, severity,
  options, and open action.
- Decision modal with:
  - decision id, raised-by agent, heartbeat age;
  - question;
  - agent reasoning or explicit unavailable state;
  - options with risk, pros, cons, affected workstreams/files when available;
  - autonomous fallback countdown or unavailable state;
  - optional audit note field;
  - defer, reject, approve command-preview actions.

Workstream 07 decision status: implemented in the bundled dependency-free
dashboard. Decision rows open a contextual modal with source/heartbeat/
workstream metadata, explicit unavailable reasoning/fallback states, audit-note
input, option selection, and `de resolve-decision` or chat-mediated previews.

## Required Capabilities

- Capability profile table with profile, bound agents, grants, escalation count,
  violation count, and status.
- Grants rendered as chips with high-risk indication.
- Review escalation action.
- Capability modal with:
  - requested agent/profile transition;
  - reason;
  - capability diff;
  - scope checkboxes;
  - TTL controls `15m`, `30m`, `1h`, `2h`, `4h`;
  - prior violations;
  - deny, deny-and-pause, grant command-preview actions.

Workstream 07 capability status: implemented in the bundled dependency-free
dashboard. Capability profile rows, pending capability decisions, violations,
and agent-detail capability controls open a read-only review modal with scope,
TTL, audit-note, prior-violation, protocol-resolution command, and
chat-mediated grant/deny previews.

Workstream 07 modal status: the shared modal shell now covers tail/status JSON,
cancel preview, keyboard help, run selector, and agent-detail log/report/
cancel/capability previews. Write-like actions remain read-only and render
command previews or explicit unavailable states.

## Required Validators

- Validator panel with registered/running/passed/blocked/skipped summary.
- Validator rows with status dot, name, command, agent, duration, count, note,
  and status pill.

## Required Alerts

- Alerts list with severity, id, message, target, relative time.
- Lifecycle and protocol alerts surfaced from real state.
- Violation toast in `violation-flash` state.
- Disconnected banner in `disconnected` state.
- Coordinator-dead alert treatment.

## Required History And Run Switcher

- Sidebar recent runs list.
- Breadcrumb run switcher popover:
  - list active/recent runs;
  - current run active state;
  - pick action switches context or previews how to open that run.
- History screen:
  - history table with run, repo, plan, started, duration, workers,
    decisions, outcome;
  - filter/search affordance;
  - export CSV affordance;
  - two-run selection;
  - comparison drawer showing duration, workers, decisions, files changed,
    tests, status, and deltas.

Workstream 08 status: implemented in the bundled dependency-free dashboard.
`/api/history` remains the canonical live source and now returns stable
read-only fields derived from run, agent, decision, report, validation, and
dashboard evidence. The sidebar recent-runs list and breadcrumb switcher show
current-run active state; selecting the current run is a no-op, while selecting
another run opens a command preview for `de dashboard --run-id ... --detach
--json` instead of mutating server context. The history screen supports
case-insensitive filtering, explicit no-results and no-history states,
client-side CSV export from loaded rows, two-run selection with oldest
replacement, and comparison deltas with `not exposed` states for missing
duration, files, tests, or terminal outcome fields.

## Required Modals

- Generic modal shell with title, subtitle, close button, backdrop click close,
  `Escape` close, body, footer, danger styling.
- Command modal for `tail` and `status`:
  - tail renders terminal-like log lines;
  - status renders structured JSON with indentation.
- Cancel run modal:
  - reason textarea;
  - in-flight tool call toggle;
  - keep-artifacts toggle;
  - affected agents/workstreams/decisions impact grid;
  - exact command preview;
  - keep-running and cancel-run command-preview buttons.
- Decision modal.
- Capability modal.
- Keyboard help modal.
- Run switcher popover.

## Required Tweaks Panel Semantics

The production dashboard does not need the host edit-mode persistence protocol,
but it must preserve user-facing tweak controls that are relevant to the
prototype:

- theme selection;
- density/zoom selection;
- scenario selection when running in fixture/demo validation mode.

If a fixture/demo mode is added for validation, it must be clearly separated
from real run state and must not pollute production `.dispatch/`.

## Required Data Mapping

Prototype mock model fields must be mapped to live data or empty states:

- `RUN` -> `/api/status`, supervisor/cancellation/failure records.
- `WORKSTREAMS` -> run workstreams, workstream files, workstream events.
- `AGENTS` -> `status.agents`, agent records, launch evidence, reports,
  heartbeats, logs.
- `DECISIONS` -> pending decisions, autonomous decisions, decisions JSONL.
- `ALERTS` -> `/api/alerts`, lifecycle diagnostics, protocol violations.
- `HISTORY` -> `/api/history`.
- `VALIDATORS` -> validation reports and validator agents.
- `PLAN_TREE` -> imported plan/workstream dependencies.
- `EVENT_TEMPLATES` -> real `/api/events` and `/api/tail`; no fake live events
  in production mode.
- `COORD_LOG` -> `/api/logs/coordinator`.

## Parity Validation Matrix

Final acceptance requires:

- Desktop screenshot for every screen.
- Mobile screenshot for every screen.
- Theme screenshots or automated smoke check for all six themes.
- Density screenshots or automated smoke check for all four density values.
- Agent card click opens detail and back navigation returns to roster.
- Each modal opens and closes by click and `Escape`.
- Keyboard shortcuts work.
- Plan search filters rows and clear restores them.
- Run switcher opens and can select/preview another run.
- History compare selects two runs and shows comparison drawer.
- Empty and terminal/disconnected/violation states are visibly distinct.
- Browser console has no dashboard-origin errors or warnings.
- Footer event tail can be collapsed, expanded, filtered, and resized by
  dragging its top edge. The resize preference is browser-local only, collapsed
  mode does not reserve the expanded height, and the collapse/expand button
  remains in the tail block's top-right corner on narrow viewports.
- Existing CLI/unit validations still pass:
  - `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`
  - `PYTHONPATH=scripts python3 -m unittest discover -s tests`
  - `python3 scripts/de.py dashboard --help`
  - `git diff --check`

## Workstream 10 Parity Matrix

This matrix records the worker-side parity audit against the repo-captured
prototype fixture. Browser screenshot and console evidence for desktop/mobile
viewports is coordinator-owned for run `20260505T095306005146Z`; this worker
did not start services or capture screenshots.

| Surface | Prototype source | Production file/selector | Data source | Mode | Desktop evidence | Mobile evidence | Automated coverage | Status | Gap/follow-up |
|---|---|---|---|---|---|---|---|---|---|
| App shell, sidebar, brand, nav badges, recent runs | `Dispatch Engine Dashboard.html`, `components.jsx`, `styles.css` | `dashboard/index.html`; `.app-shell`, `.sidebar`, `.brand-mark`, `.nav`, `.run-list` | `/api/status`, `/api/history`, fixture history | live | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset serving test, history API test | pass | Final visual spacing/icon check remains coordinator-owned. |
| Topbar breadcrumbs, run selector, clock, API state, command buttons | `components.jsx`, `styles.css` | `.topbar`, `.crumb-run`, `.run-switcher`, `.clock`, `.icon-button` | `/api/status`, `/api/history` | live | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset serving test checks run switcher and modal code | pass | Final hover/active/disabled visual check remains coordinator-owned. |
| Event stream and terminal tail | `components.jsx`, `data.js` `EVENT_TEMPLATES`, `COORD_LOG` | `.footer-tail`, `.tail-resize`, `renderEventTail`, `renderTailModal` | `/api/events`, `/api/tail`, `/api/logs/coordinator`, browser-local tail height preference | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | API no-mutation test, static modal/resize checks | pass-empty | Live event data can be empty; surface remains visible. |
| Overview scenario run header, progress, stats, tags | `components.jsx`, `scenarios.jsx`, `scratch/01-running.png` | `.run-hero`, `.scenario-progress`, `.scenario-tags`, `renderOverview` | `/api/status`, `/api/alerts`, fixture mode | live/fixture-only | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset serving test checks scenario adapter | pass-fixture | Rare visual states require `?fixture=<scenario>` evidence by coordinator. |
| Empty dashboard shell | `scenarios.jsx`, `scratch/02-empty.png` | `.empty-dashboard`, `renderEmptyDashboard` | `/api/status`, `/api/history`, fixture `empty` | empty-state/fixture-only | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset serving test checks empty labels | pass-fixture | Live no-run state depends on coordinator fixture/browser exercise. |
| Agents roster | `components.jsx`, `data.js` `AGENTS` | `.agent-grid`, `.agent-card`, `renderAgents` | `/api/status` agent records | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | agent detail API tests, static asset test | pass-empty | Runtime may not expose rich task/profile data for every agent; visible empty states are retained. |
| Agent detail screen | `screens.jsx` | `.agent-detail`, `.agent-toolbar`, `.hb-mini`, `renderAgentDetail` | `/api/agent/<agent-id>`, `/api/logs/agent/<agent-id>`, `/api/report/<agent-id>` | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | agent detail API test and 404 no-mutation test | pass-empty | Missing report, changed files, heartbeat samples, and exercised capabilities are explicit empty states. |
| Workstreams and plan tree | `components.jsx`, `screens.jsx`, `scenarios.jsx` plan search | `.plan-screen`, `.plan-tree`, `.plan-search-input`, `.coord-terminal` | `/api/plan`, `/api/logs/coordinator`, `/api/status` | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | plan API test, static asset test | pass-empty | Imported plan absence renders "No plan tree available"; no runtime follow-up for this RFC. |
| Decisions list and decision modal | `components.jsx`, `modals.jsx`, `data.js` `DECISIONS` | `.decision-row`, `.modal`, `renderDecisionModal` | `/api/status` next actions, `/api/alerts`, decisions evidence when exposed | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset test checks `resolve-decision`, modal shell | pass-empty | Runtime does not always expose reasoning, fallback countdown, affected files, or option risk; visible unavailable states remain. |
| Capability table and review modal | `screens.jsx`, `modals.jsx`, `data.js` capability profiles | `.capability-row`, `.option-row`, `.ttl-row`, `renderCapabilityModal` | `/api/status` capability profiles, `/api/alerts`, `/api/agent/<agent-id>` | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset test checks TTL, capability modal, protocol preview | pass-empty | Capability TTL/scope changes are browser-only preview controls; persisted runtime grant metadata remains not exposed. |
| Validators panel | `screens.jsx`, `data.js` `VALIDATORS` | `.validator-row`, `renderValidators` | `/api/status` validator agents and validation reports via history/report readers | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset serving test, history validation-count test | pass-empty | Command duration/count fields are present only when reports expose them. |
| Alerts and violation overlays | `components.jsx`, `scenarios.jsx`, `data.js` `ALERTS` | `.alert-row`, `.scenario-banner`, `.run-hero.state-violation-flash` | `/api/alerts`, `/api/status` protocol/capability diagnostics, fixture mode | live/fixture-only | coordinator-owned screenshot pending | coordinator-owned screenshot pending | API no-mutation test, static asset test checks violation state | pass-fixture | Violation flash visual proof requires fixture-mode browser evidence. |
| History table, filter/export, two-run compare | `screens.jsx`, `scenarios.jsx`, `data.js` `HISTORY` | `.history-screen`, `.history-toolbar`, `.rh-compare`, `exportHistoryCsv` | `/api/history` | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | history API derived-field tests, static asset test | pass-empty | Missing files/tests/terminal deltas render `not exposed` values. |
| Run switcher popover and run open preview | `components.jsx`, `modals.jsx` | `.run-switcher`, `.run-switcher-row`, `renderRunOpenPreview` | `/api/history`, current `/api/status` run id | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | history API test, static asset test | pass-empty | Cross-run switching remains command preview until multi-run server context is specified. |
| Modals: tail, status JSON, cancel preview, keyboard, run selector, agent previews | `modals.jsx`, `components.jsx` command modal | `.modal-bg`, `.modal`, `.modal-close`, `.command-block`, `renderModal` | `/api/status`, `/api/tail`, `/api/logs/coordinator`, `/api/agent/<agent-id>`, `/api/report/<agent-id>`, `/api/history` | live/empty-state | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset test checks modal strings and command preview markers | pass-empty | Final click/Escape proof remains coordinator-owned. |
| Keyboard shortcuts and input immunity | `Dispatch Engine Dashboard.html`, `components.jsx`, `modals.jsx` | `onKeyDown`, `SHORTCUTS`, `isTypingTarget` | browser state only | live | coordinator-owned interaction evidence pending | coordinator-owned interaction evidence pending | static asset test checks keyboard help; source audit verifies input/select/contenteditable guard | pass | Browser smoke remains coordinator-owned by prompt. |
| Themes: default, solar, carbon, indigo, forest, crimson | `themes.css`, `components.jsx`, `scratch/zoom.png` | `:root[data-theme]`, `.theme-row`, `setTheme`, `localStorage` keys | browser local storage only | live | coordinator-owned theme screenshots pending | coordinator-owned theme screenshots pending | static asset test checks theme presets and CSS attributes | pass | Final contrast comparison remains coordinator-owned. |
| Density/zoom: 70%, 80%, 90%, 100% | `components.jsx`, `tweaks-panel.jsx`, `scratch/zoom.png` | `.ui-zoomed`, `.zoom-button`, `setZoom`, `stepZoom` | browser local storage only | live | coordinator-owned density screenshots pending | coordinator-owned density screenshots pending | static asset test checks density preference key and CSS | pass | Final overlap check remains coordinator-owned. |
| Scenario catalog: empty, starting, running, waiting-input, violation-flash, disconnected, coordinator-dead, completed, cancelled, failed | `scenarios.jsx` | `SCENARIO_IDS`, `.fixture-strip`, `fixtureStatus`, `dashboardScenario` | live derivation from `/api/status` and `/api/alerts`; browser-only fixture mode | live/fixture-only | coordinator-owned fixture screenshots pending | coordinator-owned fixture screenshots pending | static asset test checks scenario ids/fixture mode | pass-fixture | Rare states require coordinator browser fixture capture. |
| Iconography, icon-only controls, status marks, favicon, hit targets, tooltips | `components.jsx`, `screens.jsx`, `modals.jsx`, `styles.css`, inline favicon in `dashboard/index.html` | `.icon-button`, `.btn-sm`, `.dot`, `.brand-mark`, `.modal-close`, title attributes | browser DOM/CSS only | live | coordinator-owned icon audit screenshot pending | coordinator-owned icon audit screenshot pending | static asset test checks favicon, title-backed controls, icon styles | pass | Production uses text glyphs for some dependency-free icon buttons while preserving labels, hit targets, and states; final visual acceptance remains coordinator-owned. |
| Responsive desktop/mobile placement | `styles.css`, `scratch/*.png` | `@media`, `.content`, `.grid`, `.topbar`, `.sidebar`, `.modal` | CSS/browser layout | live | coordinator-owned `1440x900` screenshots pending | coordinator-owned `390x844` screenshots pending | `git diff --check`; static asset serving test | pass | Prompt assigns browser screenshots/console evidence to main coordinator. |
| Tweaks panel user-facing semantics | `tweaks-panel.jsx` | settings popover theme/density controls; fixture query links | browser local storage and query string | live/fixture-only | coordinator-owned screenshot pending | coordinator-owned screenshot pending | static asset test checks settings popover, fixture mode, theme/density keys | pass-fixture | Host edit-mode persistence protocol intentionally out of production scope. |

## Data Parity Report

| Prototype field or surface | Production source | Mode | Follow-up |
|---|---|---|---|
| `RUN.id`, `short`, `repo`, `repoPath`, `plan`, `provider`, `mode`, `startedAt`, `status`, `coordinator`, `objective` | `/api/status`, `.dispatch/runs/<run-id>/run.json`, state directory path inference | live/empty-state | No follow-up for core fields; absent optional fields render unavailable labels. |
| Scenario lifecycle fields: started, running, waiting input, disconnected, coordinator dead, completed, cancelled, failed | `/api/status`, `/api/alerts`, supervisor diagnostics, terminal/cancellation/failure fields, fixture mode | live/fixture-only | Rich rare-state examples are fixture-only unless a real run naturally reaches that state. |
| `WORKSTREAMS.id`, `name`, `assignee`, `status`, `pct`, `files`, `blockedReason` | `/api/plan`, `/api/status` workstream assignments/counts, `/api/events`, alerts | live/empty-state | Exact percent complete is derived from status counts when available; otherwise omitted with empty-state copy. |
| `AGENTS.id`, `role`, `status`, `task`, `profile`, `caps`, `hb`, `lastHb`, `files`, `exec` | `/api/status`, `/api/agent/<agent-id>`, heartbeat files, reports, launch metadata | live/empty-state | Launch command and rich task metadata are not guaranteed for old runs; detail panels retain unavailable states. |
| Agent stdout/stderr, report, prompt/report/log paths, changed files | `/api/agent/<agent-id>`, `/api/logs/agent/<agent-id>`, `/api/report/<agent-id>` | live/empty-state | No report yet, no logs, and no changed files are explicit states. |
| Agent heartbeat history mini-chart | heartbeat JSONL samples read by `/api/agent/<agent-id>` | live/empty-state | Old runs without heartbeat samples show "No heartbeat samples recorded." |
| Agent capability grants, exercised capabilities, escalation state | agent capability profile and worker/reviewer/validator reports via `/api/agent/<agent-id>` | live/empty-state | Escalation TTL/scope history is not consistently exposed; modal uses browser-only preview controls. |
| `DECISIONS.id`, question, raised-by, since/heartbeat age, severity, options | `/api/status` next actions, `/api/alerts`, decisions evidence when available | live/empty-state | Rationale, option risk/pros/cons, affected files, and fallback countdown remain unavailable unless runtime records them. |
| `ALERTS.id`, level/severity, message, target, relative time | `/api/alerts`, `/api/status` lifecycle/protocol diagnostics | live/empty-state | No follow-up; missing alert targets render generic unavailable text. |
| `HISTORY.id`, repo, plan, started, duration, status, workers, decisions, files changed, tests, terminal reason | `/api/history` derived from run metadata, agent registry, decisions, reports, validation reports, dashboard metadata | live/empty-state | Missing duration/files/tests/terminal reason render `not exposed`; richer terminal reason taxonomy is a future runtime enhancement. |
| `VALIDATORS.name`, command, agent, status, duration, count, note | validator agents and validation/report records via `/api/status`, `/api/history`, `/api/report/<agent-id>` | live/empty-state | Duration/count/note depend on report schema completeness. |
| `PLAN_TREE` recursive phases, dependencies, selected row, file/validation metadata | `/api/plan` imported dispatch plan and workstream records | live/empty-state | No follow-up; absent imported plan shows the prototype slot with empty copy. |
| `EVENT_TEMPLATES` streaming feed | `/api/events`, `/api/tail` | live/empty-state | Production does not synthesize fake live events; empty feed remains visible. |
| `COORD_LOG` stdout/stderr | `/api/logs/coordinator`, `/api/tail` | live/empty-state | Missing log files render explicit empty terminal panels. |
| Theme and density preferences | `localStorage` keys `dispatch-engine.dashboard.theme` and `dispatch-engine.dashboard.zoom` | live | No runtime follow-up; preferences are intentionally browser-only. |
| Fixture/demo scenario data | `?fixture=<scenario>` browser-only adapter | fixture-only | Must remain visibly labeled and must not write `.dispatch/` evidence. |
| Write-like actions: cancel, resolve decision, grant/deny capability, run switch | command preview modals and chat-mediated instructions | empty-state | Direct dashboard mutation is deferred until a secure write-action protocol exists. |

## Icon Audit

| Icon or glyph surface | Prototype source | Production selector/asset | Status | Notes |
|---|---|---|---|---|
| Favicon / brand mark | Prototype title/brand mark; no separate `.ico` asset in fixture | `dashboard/index.html` inline SVG favicon; `.brand-mark` | pass | Dependency-free inline SVG and `de` brand mark preserve the prototype identity slot. |
| Topbar tail/status/settings/keyboard/cancel controls | `components.jsx` SVG icon buttons | `.topbar .icon-button`, `renderSettingsControl` | pass | Controls use dependency-free inline SVG icons with title tooltips, fixed hit targets, hover/active/danger styling, and prototype stroke weight. |
| Modal close control | `modals.jsx` close `x` | `.modal-close` | pass | Close button is present with title and Escape/backdrop support. |
| Status dots and pills | `components.jsx`, `screens.jsx`, `styles.css` | `.dot`, `.pill`, `statusPill` | pass | Tone mapping is shared across rows, run switcher, alerts, and scenario banners. |
| Plan search/clear and tree affordances | `scenarios.jsx`, `screens.jsx` | `.search-icon`, `.plan-clear`, `.plan-node` | pass | Search icon is inline SVG; clear, selected, expanded, and matched text states are present. |
| Agent detail toolbar | `screens.jsx` SVG toolbar icons | `.agent-toolbar .icon-button` | pass | Back, refresh, logs, report, capability, and cancel-preview controls use inline SVG icons with titles. |
| History filter/export/compare controls | `screens.jsx`, `scenarios.jsx` | `.history-toolbar`, `.history-compare-toggle`, `.rh-compare` | pass | Filter, export, two-run selection, active state, and clear control are present. |
| Theme swatch and check mark | `components.jsx`, `themes.css` | `.theme-swatch`, `.theme-check`, `.theme-row.active` | pass | Active theme check mark is inline SVG and swatch visual slots are implemented. |
| Density buttons | `components.jsx`, `tweaks-panel.jsx` | `.zoom-button`, `.ttl-row .zoom-button` | pass | Density and TTL segmented controls use active/hover states. |
| Scenario banners and violation toast glyphs | `scenarios.jsx` | `.scenario-banner .dot`, `.run-hero.state-violation-flash` | pass-fixture | Visual proof is coordinator-owned through fixture-mode browser capture. |

## Validation Evidence

Worker-side automated validation for this matrix is recorded in the worker
report at
`.dispatch/runs/20260505T095306005146Z/reports/worker-010-parity-validation.json`.
Browser screenshots, responsive visual comparison, and console/network evidence
are coordinator-owned. Manual foreground validation on 2026-05-05 added
wide-screen theme evidence under `.out/screenshots/manual-parity/`:

- `current-default-1440-after.png`
- `current-solar-1440-after.png`
- `current-carbon-1440-after.png`
- `current-indigo-1440-after.png`
- `current-forest-1440-after.png`
- `current-crimson-1440-after.png`

The manual pass checked a 1440x900 viewport against the repo-captured prototype
reference screenshots. Follow-up fixes replaced text glyph icon controls with
inline SVG icons, restored the prototype-sized 220px sidebar and 26px brand
mark, removed the non-prototype page grid texture, moved overview metrics under
the progress strip, and replaced hard-coded dark surface backgrounds with
theme variables so Solar, Crimson, and default themes retain prototype-style
surface hierarchy and readable contrast.
