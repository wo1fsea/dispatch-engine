---
workstream_id: "07"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-007-modals-command-previews
branch: main
depends_on: ["02", "04", "05"]
claimed_at: 2026-05-05T09:53:06Z
lease_expires_at: 2026-05-05T11:53:06Z
updated: 2026-05-05
---

# Workstream 07: Modals And Command Previews

## Scope

Restore every read-only modal and preview surface from the repo-captured
prototype in `prototype/modals.jsx`, `prototype/components.jsx`, and the root
prototype wiring.

This workstream owns:

- Generic modal shell behavior: title, subtitle, close button, backdrop close,
  `Escape` close, body/footer slots, danger styling, focus return, and mobile
  sizing.
- Tail command modal backed by `/api/tail` and `/api/logs/coordinator`, rendered
  as terminal-like timestamp/source/message lines.
- Status JSON modal backed by `/api/status`, rendered as indented structured
  JSON with no mutation and with copy/select-friendly formatting.
- Cancel run preview modal matching the prototype cancel surface: reason field,
  in-flight tool call toggle, keep-artifacts toggle, affected
  agents/workstreams/decisions impact grid, and exact command preview.
- Decision modal for pending operator decisions: id, raised-by agent,
  heartbeat age, question, reasoning/unavailable state, options, risk,
  pros/cons, affected workstreams/files when available, autonomous fallback
  countdown/unavailable state, audit note, and defer/reject/approve command
  previews.
- Capability review modal: requested agent/profile transition, reason,
  capability diff, scope checkboxes, TTL controls for `15m`, `30m`, `1h`,
  `2h`, and `4h`, prior violations, and deny/deny-and-pause/grant command
  previews.
- Keyboard help modal with all implemented navigation and modal shortcuts.
- Agent-detail command previews for logs, report, cancel-agent, and capability
  review actions.

All write-like actions remain read-only. Buttons may preview CLI/chat actions
but must not call mutating APIs or write `.dispatch/` state.

## Acceptance

- Every prototype modal can be opened from the same visible affordance or
  keyboard shortcut:
  - `c` opens the tail modal.
  - `s` opens the status JSON modal.
  - `x` opens the cancel-run preview.
  - `?` opens keyboard help.
  - Decision rows open the decision modal.
  - Capability review buttons open the capability modal.
  - Agent detail toolbar actions open their preview/log/report surfaces.
- `Escape`, close button, and backdrop click close modal state without changing
  the selected screen, selected agent, run context, theme, or density.
- Keyboard shortcuts ignore `input`, `textarea`, `select`, and contenteditable
  targets so modal forms can be edited normally.
- Tail and status modals render live data from the read-only dashboard APIs.
  Missing tail/log/status payloads render explicit unavailable messages inside
  the modal body.
- Cancel preview shows the exact command shape the operator should ask
  interactive Codex to run, including target repo and `--run-id`. If a real
  `de cancel` command does not exist yet, the modal must visibly say that the
  action is not yet backed by a CLI command and route the operator to chat.
- Decision previews use the existing `de resolve-decision` command shape when
  possible. Missing option ids, rationale, heartbeat, or affected-file data
  remain visible as explicit unavailable fields.
- Protocol/capability previews use existing `de resolve-protocol-violation`
  command shape when they are audit resolutions. Capability grant/deny actions
  that are not backed by a real CLI command must be labeled command-preview
  only.
- Modal buttons have disabled/read-only treatment until enough preview input is
  present. Disabled buttons explain the missing input in visible text or title.
- No modal silently falls back to prototype mock facts in live mode. Rich
  examples are allowed only in an opt-in fixture mode owned by Workstream 09.
- Modals remain usable and non-overlapping at desktop and mobile widths.

## Implementation Notes

- Prefer a single modal state machine in `dashboard/app.js` with a declarative
  modal registry instead of one-off DOM fragments.
- Keep modal rendering client-side and read-only. The dashboard server should
  continue to expose only GET endpoints unless a later write-auth spec changes
  that contract.
- Normalize command-preview inputs through the same data adapter used by the
  main views:
  - run id, repo path, run status, pending decisions, and agent records from
    `/api/status`;
  - events from `/api/events` or `/api/tail`;
  - coordinator stdout/stderr from `/api/logs/coordinator`;
  - capability violations and protocol alerts from `/api/alerts` and
    capability-profile fields when exposed.
- Preserve prototype visual hierarchy: modal header, dense form rows, impact
  grid, terminal/JSON code blocks, and clear footer actions.
- Do not hard-code the prototype's mock decision reasoning or capability
  escalation data into live mode. Use fixture mode for parity screenshots and
  explicit unavailable rows for missing runtime fields.
- Agent-detail log/report buttons should show live log/report availability if
  `/api/agent/<agent-id>`, `/api/logs/agent/<agent-id>`, or
  `/api/report/<agent-id>` has been implemented by related workstreams;
  otherwise they should present the missing endpoint as a data gap.

## Validation

Run focused and broad checks:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py dashboard --help
git diff --check
```

Browser validation:

- Open a live dashboard URL and verify tail, status JSON, keyboard help, cancel
  preview, decision, capability, and agent-detail preview modals.
- Confirm each modal opens from mouse and keyboard affordances where specified.
- Confirm close button, backdrop, and `Escape` close each modal.
- Confirm no modal button mutates `.dispatch/` state; compare relevant run
  evidence before and after modal interactions.
- Capture desktop and mobile screenshots for at least tail, status JSON,
  decision, capability, and cancel preview.
- Check browser console for errors while opening and closing every modal.

## Activity Log

- 2026-05-05 codex-worker: created planned Workstream 07 spec for read-only
  modal restoration and command-preview parity.
- 2026-05-05 worker-007-modals-command-previews: claimed, implemented, and
  validated Workstream 07. The dependency-free dashboard now has a shared
  contextual modal shell with backdrop, close, and Escape handling; tail,
  status JSON, cancel, decision, capability, keyboard, run selector, and
  agent-detail preview modals; audit-note fields; TTL/scope preview controls;
  and read-only command previews for write-like actions. Validated with
  `python3 scripts/de.py dashboard --help`,
  `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`, and
  `git diff --check`; browser screenshot validation remains coordinator-owned
  because this worker's capability profile allows only the listed command
  validation.
