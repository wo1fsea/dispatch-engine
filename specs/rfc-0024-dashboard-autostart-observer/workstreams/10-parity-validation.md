---
workstream_id: "10"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-010-parity-validation
depends_on: ["04", "05", "06", "07", "08", "09"]
updated: 2026-05-05
---

# Workstream 10: Prototype Parity Validation

## Scope

Validate the completed dashboard against the repo-captured prototype fixture
and produce the final parity evidence package.

This workstream owns:

- Full prototype parity validation matrix.
- Real runtime data availability and missing-field report.
- Desktop and mobile browser evidence.
- Strict visual-design parity against the prototype, including iconography,
  icon-only controls, SVG/ico assets when present, spacing, stroke weight,
  hover/active/disabled states, tooltip behavior, and responsive placement.
- Theme/density, keyboard, modal, state, run switcher, history, agent-detail,
  plan-search, and comparison smoke checks.
- Focused and broad automated tests needed to make the parity claim credible.

## Acceptance

- A parity validation matrix is added to the RFC evidence or completion report
  and covers every prototype source file:
  - `Dispatch Engine Dashboard.html`;
  - `styles.css`;
  - `themes.css`;
  - `data.js`;
  - `components.jsx`;
  - `screens.jsx`;
  - `modals.jsx`;
  - `scenarios.jsx`;
  - `tweaks-panel.jsx`;
  - `scratch/01-running.png`, `scratch/02-empty.png`, and `scratch/zoom.png`.
- The matrix includes, at minimum, these columns:
  `surface`, `prototype source`, `production file/selector`, `data source`,
  `mode`, `desktop evidence`, `mobile evidence`, `automated coverage`,
  `status`, and `gap/follow-up`.
- The matrix covers these surface groups:
  - app shell, sidebar, topbar, breadcrumbs, event stream;
  - every icon, icon-only button, status mark, visual glyph, favicon/ico asset
    when present, tooltip, hover/active/disabled state, and icon hit target;
  - all screens: overview, agents, plan, decisions, capabilities, validators,
    alerts, history, and agent detail;
  - themes: default/mission cyan, solar, carbon, indigo, forest, crimson;
  - density/zoom: `70%`, `80%`, `90%`, `100%`;
  - keyboard shortcuts: `?`, `Escape`, `x`, `c`, `s`, `g o`, `g a`, `g p`,
    `g d`, `g c`, `g v`, `g h`;
  - all modals and command previews from Workstream 07;
  - run switcher, history filter/export, and two-run comparison from
    Workstream 08;
  - all scenario states from Workstream 09;
  - plan tree search, expand/collapse, selected rows, and coordinator log;
  - clickable agent roster and agent-detail panels;
  - responsive desktop/mobile layout and console-error checks.
- A real runtime data parity report is produced. For every prototype data field
  or surface, it lists the current production source, one of `live`,
  `empty-state`, `fixture-only`, or `blocked`, and the follow-up issue/spec
  needed for missing Dispatch Engine runtime data.
- Missing real runtime data is reported explicitly. The final report must not
  claim parity by hiding missing agent detail, report, heartbeat history,
  capability TTL, affected files, test counts, terminal reason, or comparison
  deltas.
- Browser evidence includes both live-mode evidence and fixture-mode evidence
  where live state cannot naturally produce a required prototype scenario.
- Final acceptance must compare production screenshots against the prototype
  fixture, not only check that features exist. Layout, typography, density,
  color, spacing, icon shape/stroke/size, and button/icon states must be close
  enough that any visible difference is either corrected or explicitly listed
  as a blocking/deferred gap.
- Desktop evidence covers at least `1440x900`; mobile evidence covers at least
  `390x844` or another narrow viewport documented in the report.
- Evidence filenames are stable and grouped under a run-specific directory,
  for example `.out/screenshots/rfc-0024-dashboard-autostart-observer/`.
- Browser validation records console errors and network/API failures. Any
  non-benign error is either fixed or listed as a blocking gap.
- Automated tests pass before the workstream is marked validated.

## Implementation Notes

- Treat `PROTOTYPE_PARITY.md` as the source of truth for required parity, and
  treat `prototype/` as the inspectable fixture.
- Suggested matrix status values:
  - `pass`: live production surface matches prototype behavior and has
    evidence;
  - `pass-empty`: surface is present with reviewed empty/unavailable live data;
  - `pass-fixture`: surface requires fixture mode for the scenario but live
    mode does not use mock data;
  - `blocked`: required behavior or data source is missing;
  - `deferred`: explicitly out of this RFC and accepted by maintainer review.
- Suggested data source labels:
  - `/api/status`;
  - `/api/events`;
  - `/api/alerts`;
  - `/api/tail`;
  - `/api/logs/coordinator`;
  - `/api/history`;
  - `/api/agent/<agent-id>` if implemented;
  - `/api/logs/agent/<agent-id>` if implemented;
  - `/api/report/<agent-id>` if implemented;
  - fixture mode;
  - not yet exposed.
- Use screenshots plus interaction notes, not screenshots alone. For each
  interaction surface, record the action performed and expected result.
- Include a dedicated icon audit section. For each topbar, sidebar, modal,
  row-action, status, theme, density, agent-detail, plan-tree, history, and
  scenario icon, record the prototype source, production selector or asset,
  pass/fail status, and any accepted deviation.
- When a missing runtime/API field is Dispatch Engine-owned, prepare follow-up
  text using `references/issue-reporting-protocol.md`.
- Do not mark this workstream validated until Workstreams 04-09 are at least
  implemented enough to inspect.

## Validation

Required commands:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py dashboard --help
git diff --check
```

Required browser checks:

- Launch or reuse a live dashboard with:

```bash
python3 scripts/de.py dashboard <repo> --run-id <run-id> --detach --json
```

- Capture desktop and mobile screenshots for:
  - overview live mode;
  - agents and one agent detail;
  - plan search and coordinator log;
  - decisions and decision modal;
  - capabilities and capability modal;
  - validators;
  - alerts;
  - history filtered view and two-run comparison;
  - run switcher;
  - tail, status JSON, cancel preview, and keyboard help;
  - empty, waiting-input, violation, disconnected, coordinator-dead,
    completed, cancelled, failed, and fixture-mode label.
- Switch all theme presets and all density options, checking for readable
  contrast, no overlap, and no blank panels.
- Compare icon rendering against the prototype fixture in default and at least
  one alternate theme, including icon-only buttons, status dots, modal close
  controls, toolbar actions, row actions, run switcher, agent detail toolbar,
  plan tree affordances, and any favicon/ico asset present in the prototype.
- Exercise all keyboard shortcuts and confirm input/textarea fields are not
  hijacked.
- Verify fixture/demo mode is visibly labeled and does not mutate `.dispatch/`
  evidence.
- Check browser console and network logs for errors after each interaction
  group.

## Activity Log

- 2026-05-05 codex-worker: created planned Workstream 10 spec for final
  prototype parity matrix, missing runtime data report, browser evidence, and
  test validation.
- 2026-05-05 codex: tightened final acceptance to require strict prototype
  visual-design parity, including icon/ico/icon-only control audit.
- 2026-05-05 worker-010-parity-validation: claimed Workstream 10 for the
  run-scoped parity matrix and data parity report. Browser screenshots and
  console evidence remain coordinator-owned per worker prompt.
- 2026-05-05 worker-010-parity-validation: completed worker-side validation
  with dashboard help, focused observer tests, full unittest discovery, and
  `git diff --check`. `PROTOTYPE_PARITY.md` now records the parity matrix,
  data parity report, and icon audit; browser visual evidence remains
  coordinator-owned.
