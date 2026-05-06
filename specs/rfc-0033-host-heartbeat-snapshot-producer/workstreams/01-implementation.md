---
workstream_id: 01-implementation
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-001
branch:
pr:
files:
  - scripts/dispatch_engine/cli.py
  - scripts/dispatch_engine/dashboard.py
  - dashboard/app.js
  - references/heartbeat-observation.md
  - references/operator-flow.md
  - references/operator-guide.md
  - references/prompts/coordinator-protocol.md
  - SKILL.md
  - tests/test_dashboard_observer.py
  - tests/test_codex_facing_control_surface.py
  - tests/test_run_dry_run.py
  - specs/rfc-0033-host-heartbeat-snapshot-producer/
depends_on: []
updated: 2026-05-06
claimed_at: 2026-05-06T08:08:44Z
lease_expires_at: 2026-05-06T10:08:44Z
---

# Workstream 01: Host Heartbeat Snapshot Producer

Add the Codex-facing snapshot writer and update heartbeat guidance so the
dashboard has live host heartbeat state during detached runs.

Validation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
python3 scripts/de.py record-host-heartbeat --help
rg -n "record-host-heartbeat|host heartbeat|interactive Codex heartbeat producer|synthes" SKILL.md references scripts tests specs/rfc-0033-host-heartbeat-snapshot-producer
git diff --check
```

## Activity Log

- 2026-05-06 worker-003-host-heartbeat-snapshot: claimed and started
  implementation for Dispatch Engine run `20260506T044226912184Z`.
- 2026-05-06 worker-003-host-heartbeat-snapshot: validated the
  `record-host-heartbeat` writer, run-scoped dashboard read side, docs, and
  whitespace checks.
- 2026-05-06 worker-001: claimed the workstream for Dispatch Engine run
  `20260506T080338588542Z` to repair the producer boundary after coordinator
  flow used `codex-thread-heartbeat-20260506T044226912184Z` as a synthetic
  automation id.
- 2026-05-06 worker-001: added the synthetic coordinator automation id
  regression, added the CLI guard, updated heartbeat/operator guidance, and
  completed assigned validation.
- 2026-05-06 worker-001: added the coordinator dry-run prompt regression and
  prompt contract for Dispatch Engine run `20260506T083353174850Z`.

## TDD Evidence

- Red: `tests.test_codex_facing_control_surface` and
  `tests.test_dashboard_observer` failed because `record-host-heartbeat` was
  not a known command; the dashboard narrowing test failed because a legacy
  non-run-scoped snapshot was accepted.
- Green: both focused tests passed after adding the CLI writer and narrowing
  dashboard reads to `.dispatch/runs/<run-id>/host-heartbeat.json`.
- Broader validation: full assigned dashboard/control-surface suites, CLI help,
  search coverage, and `git diff --check` passed.

## Boundary Repair TDD Evidence

- Red: `PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface`
  failed because `record-host-heartbeat` accepted
  `codex-thread-heartbeat-<run-id>` and wrote the run-scoped snapshot.
- Green: the same command passed after `record-host-heartbeat` rejected the
  reserved synthetic coordinator id before writing `host-heartbeat.json`.
- Broader validation: dashboard observer suite, control-surface suite, CLI
  help, search coverage, and `git diff --check` passed for the repair.

## Coordinator Prompt Boundary TDD Evidence

- Red: `PYTHONPATH=scripts python3 -m unittest tests.test_run_dry_run` failed
  because the rendered dry-run coordinator prompt lacked the host heartbeat
  producer-boundary contract.
- Green: the same command passed after `references/prompts/coordinator-protocol.md`
  stated that real host heartbeat snapshots belong only to the outer interactive
  Codex host heartbeat and coordinators must not call `record-host-heartbeat` or
  synthesize automation ids for real runs.
- Broader validation: dry-run suite, boundary search coverage, and
  `git diff --check`.
