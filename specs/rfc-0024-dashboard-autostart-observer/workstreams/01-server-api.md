---
workstream_id: "01"
spec_id: rfc-0024-dashboard-autostart-observer
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-01-server-api
branch: main
claimed_at: 2026-05-05T16:11:51+08:00
lease_expires_at: 2026-05-05T18:11:51+08:00
updated: 2026-05-05
---

# Workstream 01: Dashboard Server Lifecycle And API

## Scope

Implement `de dashboard` with foreground/detached lifecycle, server metadata,
and read-only JSON APIs backed by existing Dispatch Engine state readers.

## Acceptance

- `de dashboard <repo> --detach --json` returns a URL.
- `--status` reports recorded service state.
- `--stop` terminates the recorded process.
- API endpoints return JSON for status, alerts, events, tail, coordinator logs,
  and history.
- Missing run and missing dashboard asset errors are Codex-readable.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
python3 scripts/de.py dashboard --help
```

## Activity Log

- 2026-05-05 worker-01-server-api: claimed and started Workstream 01 on
  `main`; scope limited to dashboard server lifecycle, read-only API, focused
  tests, and status updates.
- 2026-05-05 worker-01-server-api: implemented `de dashboard` lifecycle,
  detached `--serve` child path, run-scoped server metadata/logs, read-only
  JSON APIs, and a minimal static placeholder.
- 2026-05-05 worker-01-server-api: validated with focused dashboard tests,
  CLI help, related status/control-surface regression tests, and
  `git diff --check`.

## TDD Evidence

- Red: `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`
  failed with `ModuleNotFoundError: No module named 'dispatch_engine.dashboard'`.
- Green: `PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer`
  passed, 4 tests.
- Broader validation:
  `python3 scripts/de.py dashboard --help`;
  `PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface tests.test_status_tail`;
  `git diff --check`.
- Tests not run: full unittest discovery and browser screenshot validation;
  deferred to later workstreams/integrator because this workstream ships only
  the server/API and a placeholder static page.
