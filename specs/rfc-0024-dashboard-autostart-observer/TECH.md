---
language: en-US
audience: agent
doc_type: spec
---

# Dashboard Autostart Observer Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Dispatch Engine already exposes JSON-first control surfaces through
`status`, `events`, `alerts`, and `tail`. Interactive Codex can read those
surfaces, but users do not get a live visual panel unless they ask for status
updates manually. The repo-captured prototype fixture in
`specs/rfc-0024-dashboard-autostart-observer/prototype/` demonstrates the
desired information architecture and visual density.

Relevant files:

- `scripts/dispatch_engine/cli.py`: command registration.
- `scripts/dispatch_engine/state.py`: existing status/events/alerts readers.
- `scripts/dispatch_engine/runs.py`: run path helpers.
- `SKILL.md` and `references/operator-guide.md`: operating flow.
- New static assets under `dashboard/`.

## Change Gate

- Problem: Active DE sessions have durable state but no automatic visual
  observer panel for the user inside Codex.
- Existing path considered: Continue using `status --json`, `events`, and
  heartbeat narration only.
- Why existing path is insufficient: It keeps the chat responsive but hides
  multi-agent progress, heartbeat timing, and protocol/decision context unless
  Codex narrates every detail.
- Smallest new surface: One `dashboard` CLI command, one local read-only HTTP
  service, one static dashboard bundle, and read-only JSON endpoints.
- What will be deleted or replaced: Nothing. CLI JSON surfaces remain
  canonical and are reused by the dashboard.
- Owner: Dispatch Engine maintainers.
- Validation: unit tests for lifecycle/API, full unittest discovery, CLI help,
  `git diff --check`, and browser screenshot verification.
- Temporary or permanent: Permanent observer surface.
- Removal condition: Superseded by a host-native Codex dashboard that consumes
  the same `.dispatch/` state.

## Proposed Changes

1. Add `scripts/dispatch_engine/dashboard.py`.
   - Implement a stdlib `ThreadingHTTPServer` for local dashboard requests.
   - Serve static files from the repository/skill `dashboard/` directory.
   - Expose read-only APIs:
     - `GET /api/status`
     - `GET /api/events?since=<cursor>`
     - `GET /api/alerts`
     - `GET /api/tail`
     - `GET /api/logs/coordinator`
     - `GET /api/history`
     - `GET /api/host-heartbeat`
   - Support detached process lifecycle with `server.json`, stdout, and
     stderr logs under `.dispatch/runs/<run-id>/dashboard/`.
2. Add `de dashboard`.
   - Flags: `<repo>`, `--run-id`, `--host`, `--port`, `--detach`, `--status`,
     `--stop`, `--json`.
   - Hidden `--serve` is allowed for the detached child process.
   - Detached launches reuse an already-alive recorded service.
3. Build static dashboard assets.
   - Use plain HTML/CSS/JS so the skill is copy-installable.
   - Adapt the supplied prototype's layout into a live data-driven dashboard.
   - Keep the UI dense, utilitarian, and readable across desktop and mobile.
4. Update skill/operator guidance.
   - When interactive Codex actively starts, resumes, monitors, or supervises
     a DE run, it should launch/reuse `de dashboard --detach --json` and open
     the returned URL in the Codex in-app browser.
   - Dashboard does not replace heartbeat monitoring.
5. Add validation.
   - Tests cover API payloads, detach/status/stop lifecycle, missing run
     errors, and CLI help.
   - Browser verification covers nonblank overview and responsive layout.

## Full Prototype Backlog

The implementation must not stop at the current baseline. The prototype fixture
at `specs/rfc-0024-dashboard-autostart-observer/prototype/` includes
interaction and visual behavior that must be preserved in plain static assets:

1. Theme and density shell.
   - Port `themes.css` semantics into `dashboard/styles.css`.
   - Support `default`, `solar`, `carbon`, `indigo`, `forest`, and `crimson`
     via a `data-theme` attribute on the document root.
   - Add a settings popover in the topbar with swatches, active state, and
     density/zoom buttons.
   - Persist theme and density in `localStorage`; this is local browser UI
     preference only and must not write `.dispatch/`.
   - Workstream 04 implementation note: the dependency-free dashboard now
     applies these six presets through document-level theme attributes, stores
     preferences under `dispatch-engine.dashboard.*`, scales the full app shell
     with CSS zoom variables, and keeps `100%` as the no-override state.
2. Topbar command surfaces.
   - Add icon buttons for refresh, tail logs, status JSON, settings, keyboard
     help, and cancel preview.
   - Tail/status buttons open read-only modals backed by `/api/tail`,
     `/api/logs/coordinator`, and `/api/status`.
   - Cancel preview shows the exact `de cancel` command and requires the user
     to ask interactive Codex to execute it.
   - The footer event tail remains a persistent observation surface with
     filter buttons, collapse/expand controls, and a draggable top edge for
     resizing. The resize height is a local browser preference under
     `dispatch-engine.dashboard.tailHeight`; it must not write `.dispatch/`.
     Collapsed state ignores the custom height and keeps the toggle pinned to
     the tail block's top-right corner on desktop and narrow viewports.
3. Keyboard navigation.
   - `?` opens keyboard help.
   - `g` then `o/a/p/d/c/v/h/l` navigates to overview, agents, plan,
     decisions, capabilities, validators, history, or logs.
   - `c` opens tail logs, `s` opens status JSON, `x` opens cancel preview,
     and `Escape` closes modal/popover state.
   - Workstream 04 implementation note: shortcut routing is implemented in
     `dashboard/app.js` and ignores `input`, `textarea`, `select`, and
     contenteditable targets. Topbar tail/status/cancel surfaces are read-only
     modals backed by loaded API data or explicit unavailable text.
4. Run switcher.
   - Breadcrumb run selector opens a popover of recent local runs from
     `/api/history`.
   - Selecting a run navigates the browser to the same dashboard service with a
     run query or starts/reuses that run's dashboard service once the API
     supports safe run selection.
5. Plan explorer.
   - Build a plan/workstream tree from imported plan/run state and
     `workstream.planned` events.
   - Add search/filter, expand/collapse, status dots, selected row styling, and
     footer hints.
   - Include coordinator stdout/stderr tail in the plan screen.
   - Workstream 06 implementation note: `dashboard.py` now exposes
     `GET /api/plan` as a read-only adapter over `run.json`, workstream JSON
     files, and existing `/api/status` workstream assignment summaries. The
     static dashboard uses that endpoint for a recursive searchable plan tree,
     selected/expanded row state, dependency/file/validation metadata, explicit
     missing-plan empty states, and a coordinator stdout/stderr terminal panel
     with cached/live-tail affordance and missing-log empty states.
6. Agent roster and agent detail.
   - Agent cards are clickable.
   - Clicking an agent opens an agent detail view instead of only showing the
     generic agents grid.
   - Detail view shows status, heartbeat, role, workstream, provider/profile,
     prompt path, report path, stdout/stderr tail, recent events, changed files
     if report evidence exists, capability grants, capability escalations,
     heartbeat history, and metadata.
   - Detail actions are read-only: open logs/report/capability preview modals
     or show command previews; they do not mutate state.
   - Workstream 05 implementation note: `dashboard.py` now exposes
     `GET /api/agent/<agent-id>`, `GET /api/logs/agent/<agent-id>`, and
     `GET /api/report/<agent-id>` as read-only adapters over agent registry,
     report, heartbeat, and log files. `dashboard/app.js` uses those adapters
     for clickable coordinator/worker/reviewer/validator cards and renders
     missing report, changed-file, heartbeat, metadata, exercised capability,
     and escalation data as explicit empty states.
7. Decisions and capabilities.
   - Decision modal shows question, raised-by agent, heartbeat age,
     recommended/autonomous fallback if present, options, rationale, risk, and
     note field.
   - Capability review modal shows requested capability diff, scope, TTL
     options, prior violations, and a command preview.
   - Where runtime state does not yet expose rationale or TTL metadata, render
     an explicit empty state rather than hard-coded demo data.
   - Workstream 07 implementation note: `dashboard/app.js` now uses one
     contextual modal state for tail/status JSON, cancel preview, decisions,
     capabilities, keyboard help, run selector, and agent-detail previews.
     Decision rows render `de resolve-decision` previews when option ids are
     available; capability/protocol review renders
     `de resolve-protocol-violation` or chat-mediated grant/deny previews.
     Audit notes, reason fields, TTL controls, and scope checkboxes stay in
     browser memory and do not write `.dispatch/` state.
8. State-specific overlays.
   - Empty dashboard state when no run exists.
   - Starting, running, waiting-input, violation-flash, disconnected,
     coordinator-dead, completed, cancelled, and failed states derived from
     `status --json`, alerts, supervisor state, heartbeat recency, and
     cancellation/failure records.
   - Disconnected/coordinator-dead states must be visible even when the last
     fetched data is stale.
9. History compare.
   - History table uses `/api/history`.
   - Add filter/search and two-run comparison drawer.
   - Export is client-side CSV generation from already loaded read-only data.
   - Workstream 08 implementation note: `/api/history` now normalizes
     read-only evidence from `run.json`, agent registry files,
     `decisions.jsonl`, worker/reviewer/validator reports, and dashboard
     metadata into stable run rows with plan, repo, duration, worker/agent,
     decision, changed-file, test, terminal reason, and command-preview
     fields. The static dashboard renders sidebar recent runs, a breadcrumb
     run switcher popover, current-run no-op state, different-run
     `de dashboard --run-id ... --detach --json` previews, history filtering,
     loaded-row CSV export, two-run selection, and comparison deltas with
     explicit `not exposed` values for missing runtime fields.
   - Workstream 09 implementation note: `dashboard/app.js` now adapts live
     status, alerts, fetch health, supervisor diagnostics, pending decisions,
     protocol/capability violations, and terminal fields into one scenario
     object. The overview header renders scenario labels, subtitles, progress,
     stats, tags, banners, frozen terminal clock treatment, and an empty
     dashboard shell. Rare states can be exercised with the visibly labeled
     browser-only `?fixture=<scenario>` mode; fixture data never calls a
     mutating endpoint or writes `.dispatch/` state.
10. Validation and polish.
    - Browser screenshots for desktop and mobile.
    - Theme matrix smoke check for all presets.
    - Keyboard shortcut smoke check.
    - Agent-detail click smoke check.
    - Modal open/close smoke check.
    - No blank panels, overlapping text, inaccessible controls, or console
      errors.
   - Workstream 10 implementation note: `PROTOTYPE_PARITY.md` now contains
     the worker-side parity matrix, real runtime data parity report, and icon
     audit for every prototype source group. Browser screenshots, responsive
     visual comparison, and console/network evidence are explicitly reserved
     for the main coordinator/session for run `20260505T095306005146Z`.

## Data Completion Policy

Real Dispatch Engine run state does not yet expose every data point used by the
prototype mock model. Implement full prototype parity with a data adapter layer
instead of pruning UI:

- Production live mode reads only real dashboard APIs and `.dispatch/`-backed
  data.
- Missing fields render reviewed empty/unavailable states in the same visual
  slot that the prototype uses.
- The overview `Host heartbeat` panel reads the host-layer Codex heartbeat
  snapshot through `GET /api/host-heartbeat`. The preferred source file is
  `.dispatch/runs/<run-id>/host-heartbeat.json`; this is a run-scoped
  read-only observer input for the dashboard. If the file is missing for an
  active run, the panel must show a missing/unavailable state instead of
  inferring host heartbeat freshness from agent events. If the run is terminal,
  the panel may derive a stopped terminal state from `run.json` so stale
  countdowns are never shown.
- Fixture/demo mode may exist solely for parity validation of rare states such
  as disconnected, coordinator-dead, terminal, violation-flash, and rich agent
  detail examples. It must be opt-in and visibly marked.
- The dashboard must produce or preserve a final data parity report listing
  each prototype surface, current data source, status (`live`, `empty-state`,
  `fixture-only`, or `blocked`), and any runtime/API follow-up.
- Runtime/API gaps discovered during implementation must be reported using
  `references/issue-reporting-protocol.md` when they are Dispatch
  Engine-owned framework gaps.

## API Expansion Needed

The current API is enough for the baseline. Full prototype parity likely needs
additional read-only endpoints or richer existing payloads:

- `GET /api/agent/<agent-id>`: normalized agent detail, report summary,
  heartbeat history, launch evidence, prompt/report/log paths, changed files,
  capability profile, and related events.
- `GET /api/logs/agent/<agent-id>`: agent stdout/stderr tail.
- `GET /api/plan`: imported plan tree, workstreams, dependencies, selected run
  metadata, file/validation counts, and live assignment overlays.
- `GET /api/report/<agent-id>`: worker/reviewer/validator report JSON when it
  exists.
- `GET /api/host-heartbeat`: normalized outer Codex heartbeat observer state,
  including `automation_id`, `owner`, `interval_seconds`, raw/effective
  status, `active`, `last_wakeup_at`, `next_wakeup_at`, stop metadata, source
  path, and explicit empty states. This endpoint is read-only and must not
  create or update the heartbeat snapshot.
- `GET /api/status-raw`: exact status JSON for the status modal, or reuse
  `/api/status` and render the raw payload client-side.

Prefer extending the server with structured read-only APIs over parsing files
in browser JavaScript. All generated service metadata and dashboard process
state must remain under `.dispatch/`.

## Validation Plan

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py dashboard --help
git diff --check
```

Browser check:

```bash
python3 scripts/de.py dashboard <fixture-or-dogfood-repo> --detach --json
```

Open the returned URL in the Codex in-app browser and verify that overview,
agents, decisions, capabilities, validators, alerts, history, and event tail
render without blank panels or text overlap.

Full prototype validation additionally requires:

```text
- switch every theme preset and verify readable contrast
- switch every density/zoom option and verify no incoherent overlap
- click an agent card and verify agent detail shows live status/log/report data
- open plan search and verify filter/expand/collapse
- open status, tail, keyboard, decision, capability, run switcher, and cancel
  preview modals
- use keyboard shortcuts for navigation and modal open/close
- verify empty, terminal, disconnected, waiting-input, and violation states
  with fixtures or real run state
- verify history compare with two selected runs
```

## Risks

- Detached server processes could linger. Mitigate with `--status`, `--stop`,
  recorded PID, and reuse checks.
- Dashboard could drift from CLI semantics. Mitigate by calling existing
  runtime readers instead of parsing `.dispatch/` directly wherever possible.
- A browser UI can tempt write actions. Keep first version read-only and route
  writes through interactive Codex.

## Follow-ups

- Complete prototype parity workstreams 04-10.
- Confirmed write actions with localhost token.
- SSE event streaming instead of polling.
- Multi-run dashboard index across multiple target repositories.
