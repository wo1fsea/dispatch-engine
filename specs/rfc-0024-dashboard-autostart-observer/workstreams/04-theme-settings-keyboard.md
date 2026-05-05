---
workstream_id: "04"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-004-theme-settings-keyboard
branch: main
depends_on:
  - "02"
claimed_at: 2026-05-05T09:53:06Z
lease_expires_at: 2026-05-05T11:53:06Z
updated: 2026-05-05
---

# Workstream 04: Theme, Settings, Keyboard, And Responsive Shell

## Scope

Restore the prototype shell-level behavior that surrounds every dashboard
screen: theme presets, density/zoom settings, topbar settings/tweaks controls,
keyboard navigation, sidebar/topbar shell state, and responsive layout.

This workstream is the foundation for later prototype-parity screens. It must
not add write actions to Dispatch Engine state; all preferences are browser UI
preferences only.

## Acceptance

- Theme support matches the prototype fixture:
  - `default` / Mission cyan, `solar`, `carbon`, `indigo`, `forest`, and
    `crimson` are available.
  - The selected theme is applied instantly through a document-level
    `data-theme` attribute or equivalent root token switch.
  - The default Mission cyan theme renders without requiring a non-default
    theme attribute.
  - Theme tokens cover page, panel, nested surface, hover, selected, line,
    primary/secondary/tertiary text, accent, status, soft status, and terminal
    log colors.
  - The sidebar brand mark and status chips remain readable in every theme.
- Settings popover matches the prototype topbar behavior:
  - The settings icon opens a popover anchored under the topbar settings
    button.
  - The popover contains theme swatches, theme name/description text, active
    row styling, and a visible check mark on the active theme.
  - Density/zoom buttons are available for `70%`, `80%`, `90%`, and `100%`.
  - Clicking outside the popover or pressing `Escape` closes it.
  - Theme and density/zoom persist in `localStorage` and never write under
    `.dispatch/`.
- Density/zoom reproduces the prototype behavior:
  - Non-100% zoom applies instantly to the full app shell.
  - The implementation uses stable CSS variables or an equivalent transform
    that preserves full-viewport coverage and does not introduce blank gutters.
  - `100%` clears zoom override state.
  - Text, buttons, tables, event stream, modal overlays, and terminal panels do
    not overlap at any supported zoom.
- Topbar and sidebar shell match prototype information architecture:
  - Topbar keeps breadcrumbs, run selector affordance, elapsed/state clock,
    refresh, tail-log, status JSON, settings, keyboard-help, and cancel-preview
    buttons where applicable.
  - Sidebar keeps Dispatch Engine brand, active-run/no-active-run section,
    screen navigation, dynamic badges, and recent runs.
  - Navigation screens include `overview`, `agents`, `plan`, `decisions`,
    `capabilities`, `validators`, `alerts`, and `history`; any existing `logs`
    screen remains reachable without replacing prototype screens.
  - Empty mode visibly disables non-applicable run screens while preserving the
    overview/no-active-run shell.
- Keyboard behavior matches the prototype:
  - `?` opens keyboard help.
  - `Escape` closes an open modal/popover or clears a pending navigation chord.
  - `x` opens cancel-run preview when a cancellable run is active.
  - `c` opens coordinator tail logs.
  - `s` opens status JSON.
  - `g o`, `g a`, `g p`, `g d`, `g c`, `g v`, and `g h` navigate to
    overview, agents, plan, decisions, capabilities, validators, and history.
  - `g l` may navigate to an existing logs screen if that screen is retained.
  - `/` focuses plan or agent search when the active screen exposes search.
  - `t` cycles themes, and `+` / `-` step zoom when those shortcuts can be
    implemented without browser conflict.
  - Keyboard handlers ignore `input`, `textarea`, `select`, and contenteditable
    targets.
  - Chord state times out and does not leak across modal state.
- Keyboard help modal is complete for every implemented shortcut and closes
  with `Escape` or the modal close control.
- Responsive shell behavior matches the prototype:
  - Desktop preserves the sidebar, topbar, scrollable main content, and bottom
    event stream hierarchy.
  - Narrow widths stack or collapse shell regions without incoherent overlap.
  - Fixed-format elements such as icon buttons, badges, counters, and event
    filters keep stable dimensions across hover and live updates.

## Implementation Notes

- Use `prototype/Dispatch Engine Dashboard.html`, `prototype/components.jsx`,
  `prototype/tweaks-panel.jsx`, `prototype/styles.css`, and
  `prototype/themes.css` as the source of truth for this workstream.
- Port the prototype theme tokens into the bundled static dashboard CSS instead
  of loading the prototype files at runtime.
- Implement production settings directly in `dashboard/app.js`; do not ship
  the prototype host edit-mode protocol as a production dependency.
- Store preferences under dashboard-specific `localStorage` keys, for example
  `dispatch-engine.dashboard.theme` and `dispatch-engine.dashboard.zoom`.
- Keep all controls read-only relative to Dispatch Engine runtime state.
  Cancel, tail, and status buttons may open modal/preview surfaces, but this
  workstream must not execute `de cancel`, mutate run files, or change
  `.dispatch/` metadata.
- Treat missing real runtime fields as visible empty or unavailable states.
  Do not hard-code prototype mock counts into live mode.
- Later workstreams depend on this keyboard and responsive shell, so expose
  small reusable helpers for modal state, screen navigation, shortcut routing,
  preference loading, and root-class/theme application.

## Validation

Run baseline checks:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
python3 scripts/de.py dashboard --help
git diff --check
```

Browser validation:

- Open a live dashboard URL and verify every theme preset at desktop and mobile
  widths.
- Verify `70%`, `80%`, `90%`, and `100%` zoom on desktop and mobile with no
  blank gutters, clipped controls, or text overlap.
- Reload the browser and verify theme and zoom preferences persist.
- Exercise `?`, `Escape`, `x`, `c`, `s`, `g o`, `g a`, `g p`, `g d`, `g c`,
  `g v`, `g h`, `/`, `t`, `+`, and `-` where implemented.
- Confirm shortcuts do nothing while typing in search fields or text inputs.
- Check browser console output for uncaught errors.

## Activity Log

- 2026-05-05 codex-worker: created Workstream 04 parity spec for
  theme/settings/density/keyboard/responsive shell restoration from the
  repo-captured prototype fixture.
- 2026-05-05 worker-004-theme-settings-keyboard: claimed Workstream 04 and
  began restoring the dependency-free theme, settings, density, topbar modal,
  and keyboard shell.
- 2026-05-05 worker-004-theme-settings-keyboard: implemented the
  dependency-free settings popover, six theme presets, persisted density zoom,
  topbar command modals, keyboard help, Escape handling, and `g` navigation
  shell. Validated with `python3 scripts/de.py dashboard --help`,
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`, and
  `git diff --check`; browser screenshot validation was not run in this worker
  because the assigned capability profile allows only the listed commands and
  denies service starts.
