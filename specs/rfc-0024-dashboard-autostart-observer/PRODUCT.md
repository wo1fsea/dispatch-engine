---
language: en-US
audience: mixed
doc_type: spec
---

# Dashboard Autostart Observer Product Spec

## Summary

When interactive Codex actively uses the Dispatch Engine skill for a target
repository, it should be able to start a local dashboard service and open the
Codex in-app browser to show current Dispatch Engine progress. The dashboard is
a visual observer for `.dispatch/` run state; Codex remains the conversational
operator and decision interpreter.

The first shipped baseline is read-only and shows live run status,
workstreams, agents, decisions, alerts, capability state, validators, run
history, and event/log tails. That baseline is not the full prototype. The
full dashboard must also implement the prototype's interaction model:
theme/density controls, keyboard navigation, run switching, scenario-derived
states, searchable plan tree, clickable agent detail, modals, run history
comparison, and state-specific overlays.

## Goals / Non-goals

- Goal: Add `de dashboard` as a Codex-facing local service command.
- Goal: Return a browser URL and durable service metadata under the run state.
- Goal: Let interactive Codex open the returned URL in the Codex in-app
  browser whenever it starts or resumes active Dispatch Engine supervision.
- Goal: Ship the dashboard static assets inside the skill/repository root so
  copied skill installs work without a separate frontend build.
- Goal: Render real `.dispatch/` state through read-only JSON APIs.
- Goal: Reuse the existing dashboard prototype's control-room layout, visual
  language, and operator interaction model.
- Goal: Make every useful prototype interaction work against real `.dispatch/`
  state or a clearly read-only command preview. Do not leave prototype-only
  affordances implied but nonfunctional.
- Non-goal: Replace heartbeat wakeups, interactive Codex narration, or the
  coordinator.
- Non-goal: Provide write actions in the first version.
- Non-goal: Add Node, Vite, npm, or a compiled frontend build step.

## Behavior Invariants

1. `de dashboard <repo> --run-id <run-id> --detach --json` starts or reuses a
   local service and returns a URL suitable for the Codex in-app browser.
2. Dashboard services bind to `127.0.0.1` by default.
3. Service metadata lives under
   `.dispatch/runs/<run-id>/dashboard/server.json`.
4. Dashboard logs live under the same dashboard directory.
5. `de dashboard --status --json` reports whether the recorded service is
   alive and which URL should be opened.
6. `de dashboard --stop --json` terminates the recorded dashboard process
   without modifying run outcome or evidence.
7. The browser UI reads from the dashboard APIs and does not mutate project
   files or `.dispatch/` state.
8. If no run exists, dashboard commands fail with a Codex-readable error.
9. If the host cannot open an in-app browser, Codex reports the URL and keeps
   monitoring through CLI status surfaces.
10. The `Host heartbeat` card is a display of the outer interactive Codex
    host heartbeat, not coordinator or worker agent heartbeats. It reads a
    run-scoped `.dispatch/runs/<run-id>/host-heartbeat.json` snapshot when
    available, shows an explicit unavailable state when that snapshot is
    missing for an active run, and shows stopped/terminal treatment when the
    run is terminal.

## Prototype Completeness Scope

The full dashboard includes these prototype surfaces:

- Overview: run header, progress bars, status counts, workstreams, heartbeat,
  decisions, alerts, agents, and live event tail.
- Agents: coordinator/worker/reviewer/validator roster; clicking any agent
  opens an agent detail view with current status, role, workstream, provider,
  capability profile, prompt/report paths, recent stdout/stderr tail, file
  scope, report state, heartbeat history, and metadata. Agent detail includes
  back navigation and read-only action buttons for log/report/capability
  review.
- Plan: imported plan/workstream tree with search/filter, expand/collapse,
  status marks, workstream detail, and coordinator log tail.
- Decisions: pending decision cards, autonomous-decision summary, decision
  detail modal, option comparison, risk/pro/con display, audit-note field, and
  command preview for chat-mediated resolution.
- Capabilities: capability profile summary, grants, high-risk modes,
  escalations, unresolved/resolved protocol violations, capability review modal,
  TTL/scope preview, and command preview for chat-mediated resolution.
- Validators: validator evidence and report status.
- Alerts: material alerts, lifecycle diagnostics, violation toasts, disconnected
  event-stream banner, coordinator-dead warning, and state-specific severity.
- History: recent local run directories for the target repository, filtering,
  two-run comparison, and export-ready client-side table data.
- Settings: topbar settings popover with theme presets and density/zoom
  controls.
- Themes: support the prototype presets `default`, `solar`, `carbon`,
  `indigo`, `forest`, and `crimson` without external assets or build steps.
- Keyboard: `?` opens keyboard help; `g` + screen letters navigates; `x`, `c`,
  and `s` open cancel, tail, and status surfaces where available.
- Run switcher: breadcrumb run selector lists recent runs and can switch the
  read-only dashboard context when the API supports selecting another local
  run.
- Empty and terminal states: no active run, starting, running, waiting for user
  input, violation flash, disconnected stream, coordinator dead, completed,
  cancelled, and failed states all have distinct read-only UI treatment.
- Modals: command/status modal, tail modal, cancel confirmation, decision
  review, capability escalation review, keyboard help, and run switcher.

## Baseline Already Implemented

The current implementation covers the local service, read-only API, overview,
basic navigation, basic workstream/agent/decision/capability/validator/alert/
history/log views, static asset serving, browser autostart guidance, and
responsive rendering. It does not yet satisfy the complete prototype scope
above.

## Read-only Action Rule

Dashboard UI must not directly mutate repository files or `.dispatch/` state in
this version. Prototype write-like actions such as cancel, decision resolve, or
capability grant must be rendered as read-only previews that show the exact
Codex/`de` command or chat-mediated action to take. Actual mutation remains
owned by interactive Codex unless a later spec explicitly adds token-protected
write actions.

## Open Questions

- Should later versions expose confirmed write actions from the dashboard, or
  should all writes remain chat-mediated through Codex?
- Should the dashboard service require a localhost token before write actions
  are added?
