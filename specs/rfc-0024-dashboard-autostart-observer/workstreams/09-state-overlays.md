---
workstream_id: "09"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-009-state-overlays
depends_on: ["02", "04"]
updated: 2026-05-05
---

# Workstream 09: State Overlays And Fixture Mode

## Scope

Restore explicit state treatment from `prototype/scenarios.jsx`,
`prototype/components.jsx`, and `prototype/styles.css` while keeping live mode
grounded in real Dispatch Engine state.

This workstream owns visible states for:

- Empty/no-active-run dashboard.
- Starting and running run headers.
- Waiting-input/operator-decision state.
- Protocol violation and capability violation flash state.
- Disconnected event stream state.
- Coordinator-dead/stale-supervisor state.
- Terminal completed, cancelled, and failed states.
- Fixture/demo mode used only to exercise rare states during parity
  validation.

## Acceptance

- Empty state renders a full dashboard shell equivalent to the prototype empty
  dashboard: no-active-run topbar, recent runs, plans/recent plan placeholders
  when available, CTA-style read-only command previews, and no blank main
  content.
- Starting state is distinct from running: progress/clock can be live, but the
  header must identify launch/import/spawn progress instead of pretending all
  agents are active.
- Running state remains the normal live dashboard and keeps scenario-aware run
  header stats, tags, heartbeat treatment, event tail, and alerts.
- Waiting-input state is derived from pending decisions or decision-required
  alerts. It visibly highlights decisions in the sidebar/header, pauses or
  annotates affected workstreams, and provides a decision modal affordance.
- Protocol/capability violation state is derived from alerts, capability
  violations, or unresolved protocol violation records. It shows a toast/banner
  equivalent to the prototype violation flash with review action routed to the
  capability/protocol preview modal.
- Disconnected state is visible when event polling fails, the event stream
  cursor stops advancing beyond the accepted stale threshold, or the browser is
  using last-known data. The banner must show last successful fetch time,
  retry/attempt state when available, and a "show known data" treatment.
- Coordinator-dead state is visible when coordinator heartbeat or supervisor
  process evidence is stale beyond threshold. It must not be hidden by stale
  cached status data.
- Terminal states completed, cancelled, and failed freeze elapsed/clock
  treatment, show terminal status and reason when available, and keep artifacts
  and history affordances visible.
- Failed terminal state distinguishes validation failures, protocol failures,
  and unknown failure reason when evidence allows.
- Cancelled terminal state shows actor/reason/artifact retention when exposed;
  otherwise explicit unavailable rows remain visible.
- Fixture mode is opt-in, visibly labeled in the shell, and never writes
  `.dispatch/` state or changes live run evidence.
- Fixture mode can render `empty`, `starting`, `running`, `waiting-input`,
  `violation-flash`, `disconnected`, `coordinator-dead`, `completed`,
  `cancelled`, and `failed` for browser evidence.
- Live mode never silently uses prototype mock data. If state cannot be derived,
  render `not exposed` and include the gap in Workstream 10's data parity
  report.
- All overlays are responsive and do not cover core controls in an incoherent
  way on desktop or mobile.

## Implementation Notes

- Add a state adapter that converts live API payloads into a single dashboard
  scenario object. Suggested inputs:
  - `/api/status`: run status, run id, agent counts, coordinator/supervisor
    status, pending decisions, last event time, terminal fields if exposed;
  - `/api/events`: latest cursor movement, event timestamps, lifecycle events;
  - `/api/alerts`: pending decisions, protocol/capability violations,
    heartbeat alerts, blocked workstreams;
  - dashboard fetch failures and last successful poll time in browser state;
  - `/api/history`: terminal status/reason for prior selected runs.
- Define state precedence explicitly. Recommended order:
  1. no active run or `no_run` -> `empty`;
  2. unresolved protocol/capability violation -> `violation-flash`;
  3. coordinator heartbeat/supervisor stale -> `coordinator-dead`;
  4. event/API polling stale -> `disconnected`;
  5. pending decisions -> `waiting-input`;
  6. terminal run status -> `completed`, `cancelled`, or `failed`;
  7. launch/import/spawn in progress -> `starting`;
  8. otherwise -> `running`.
- Terminal states may override stale polling when the terminal result is
  current and trusted; document any exception in the code and parity report.
- Store fixture selection in query string or local browser storage only. It
  must be impossible for fixture selection to write under `.dispatch/`.
- Use fixture mode for validation screenshots of rare states, but keep the
  fixture label visible so evidence is not confused with live production data.
- Keep overlays accessible from keyboard and readable at reduced density/zoom
  settings.

## Validation

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py dashboard --help
git diff --check
```

Focused validation:

- Unit-test state adapter precedence for empty, starting, running,
  waiting-input, violation, disconnected, coordinator-dead, completed,
  cancelled, and failed inputs.
- Unit-test fixture mode cannot mutate run evidence and is visibly flagged in
  returned/rendered state.
- Browser-test live empty/no-run behavior when no `.dispatch/runs` exists.
- Browser-test fixture mode for every required scenario.
- Capture desktop and mobile screenshots for empty, waiting-input, violation,
  disconnected, completed, cancelled, failed, and fixture-mode label.
- Verify no overlay hides topbar controls, sidebar navigation, or event/history
  affordances on desktop or mobile.
- Verify console stays error-free while toggling fixture scenarios and while
  simulating fetch failures.

## Activity Log

- 2026-05-05 codex-worker: created planned Workstream 09 spec for explicit run
  state overlays, terminal-state treatment, disconnected handling, and
  fixture-mode parity.
- 2026-05-05 worker-009-state-overlays: implemented and validated scenario
  headers, banners, terminal frozen-clock treatment, empty dashboard shell, and
  visibly labeled browser-only fixture mode for the required state catalog.
