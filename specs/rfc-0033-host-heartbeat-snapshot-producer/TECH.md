---
language: en-US
audience: agent
doc_type: spec
---

# Host Heartbeat Snapshot Producer Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #28 came from dogfood run `20260505T182233983007Z`. The host heartbeat
automation woke interactive Codex, but no
`.dispatch/runs/<run-id>/host-heartbeat.json` was written. The dashboard
therefore derived `STOP TERMINAL` from `run.json` after completion, but could
not show live heartbeat freshness during the run.

Relevant files:

- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/dashboard.py`
- `dashboard/app.js`
- `references/heartbeat-observation.md`
- `references/operator-flow.md`
- `references/operator-guide.md`
- `SKILL.md`
- `tests/test_dashboard_observer.py`
- `tests/test_codex_facing_control_surface.py` if extended

## Change Gate

- Problem: dashboard heartbeat panel lacks a state producer.
- Smallest new surface: a Codex-facing CLI command that writes a structured
  snapshot; existing dashboard endpoint remains read-only.
- Do not implement Codex App automation creation inside Dispatch Engine.

## Proposed Changes

1. Add a CLI helper such as `record-host-heartbeat`:
   - target repo and optional `--run-id`;
   - `--automation-id`, `--owner`, `--status`, `--interval-seconds`;
   - `--last-wakeup-at`, optional `--next-wakeup-at`;
   - `--last-observed-cursor`;
   - optional `--stop-reason` / `--stopped-at`.
2. Write `.dispatch/runs/<run-id>/host-heartbeat.json` atomically.
3. Update heartbeat guidance:
   - after every status/events/alerts heartbeat check, call the writer;
   - on terminal state, write stopped status before deleting/stopping the
     host automation.
4. Add tests:
   - command writes expected snapshot;
   - `/api/host-heartbeat` reads it without mutating;
   - terminal derivation remains fallback when snapshot is missing.

## Validation Plan

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
python3 scripts/de.py record-host-heartbeat --help
rg -n "record-host-heartbeat|host-heartbeat.json|last_wakeup_at" SKILL.md references scripts tests specs/rfc-0033-host-heartbeat-snapshot-producer
git diff --check
```

## Risks

- The host may not expose exact next wakeup time. Allow deriving it from
  interval when necessary, but preserve explicit host values when supplied.
