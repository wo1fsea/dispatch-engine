---
id: 03-inspect-plan
language: en-US
audience: agent
doc_type: spec
status: validated
owner: codex-worker
branch: main
pr:
files:
  - scripts/dispatch_engine/inspect.py
  - scripts/dispatch_engine/planner.py
depends_on:
  - 01-runtime-state
claimed_at: 2026-05-02T00:00:00+08:00
lease_expires_at:
updated: 2026-05-02
---

# Inspect And Plan Workstream

## Scope

Reduce inspection noise and make planning conservative about broad or risky objectives.

## Plan

1. Deduplicate and prioritize planning-source output.
2. Keep human inspect output bounded.
3. Preserve machine-readable fields for JSON output.
4. Add conservative pending-decision heuristic for broad, risky, or multi-domain objectives.
5. Keep one workstream as the default plan.

## Progress

Validated inspect planning-source bounds/deduplication and conservative plan pending-decision behavior.

## Validation

- TDD red: `PYTHONPATH=scripts python3 -m unittest tests.test_inspect_plan` failed before implementation because inspect returned 14 planning sources instead of 8 and broad planning returned 0 decisions instead of 1.
- TDD green: `PYTHONPATH=scripts python3 -m unittest tests.test_inspect_plan` passed after implementation.
- Broader unit validation: `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- Requested CLI commands with `python` were attempted but failed because `python --version` is `Python 2.7.18`, which cannot parse `from __future__ import annotations`.
- CLI runtime validation with Python 3:
  - `python3 scripts/de.py inspect .`
  - `python3 scripts/de.py inspect . --json`
  - `python3 scripts/de.py plan . --objective "update backend API and UI flow"`
  - `python3 scripts/de.py status . --json`
  - `python3 scripts/de.py tail . --json`
- Confirmed broad objective records one pending decision and emits `decision.created`.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
- 2026-05-02 codex-worker: claimed workstream on main.
- 2026-05-02 codex-worker: validated inspect bounds/deduplication and plan pending-decision heuristic.
