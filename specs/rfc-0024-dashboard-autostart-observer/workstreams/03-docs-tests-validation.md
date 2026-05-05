---
workstream_id: "03"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-03-docs-autostart
updated: 2026-05-05
---

# Workstream 03: Docs Autostart Guidance

## Scope

Update skill/operator guidance so active Dispatch Engine sessions launch or
reuse the read-only dashboard observer and open the returned URL in the Codex
in-app browser when available.

## Acceptance

- `SKILL.md` says active DE sessions should launch/reuse `de dashboard` and
  open the returned URL in the Codex browser.
- Operator docs describe dashboard lifecycle and read-only scope.
- Docs clarify the dashboard does not replace heartbeat supervision or
  `status --json`, `events --since`, and `alerts --json` checks.
- Coordinator-level browser verification remains part of final cross-workstream
  validation, outside this worker's capability profile.

## Validation

```bash
python3 scripts/de.py dashboard --help
git diff --check
```

## Activity Log

- 2026-05-05 worker-03-docs-autostart: documented dashboard autostart,
  Codex in-app browser opening, read-only observer scope, and heartbeat/status
  supervision boundaries in the skill and operator runbooks.
- 2026-05-05 worker-03-docs-autostart: validated assigned scope with
  `python3 scripts/de.py dashboard --help` and `git diff --check`.
- 2026-05-05 worker-04-dashboard-validation: reran dashboard-focused tests with
  static asset coverage, verified `de dashboard --help`, and confirmed
  `git diff --check`. Coordinator reran
  `PYTHONPATH=scripts python3 -m unittest tests.test_removed_inspect_plan` and
  `PYTHONPATH=scripts python3 -m unittest discover -s tests` successfully after
  the dashboard command root help changed to avoid the removed `inspect`
  command wording.
- 2026-05-05 codex: verified browser evidence through the Codex browser MCP
  and recorded the validation-worker non-terminal-report dogfood issue as
  https://github.com/wo1fsea/dispatch-engine/issues/20.
