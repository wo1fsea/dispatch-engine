---
language: en-US
audience: agent
doc_type: workstream
status: validated
updated: 2026-05-02
---

# 04 - Validation And Dogfood

## Scope

Validate the observation loop against a real or fixture target run:

1. Start a detached Dispatch Engine run.
2. Query status from a separate Codex-triggered check.
3. Confirm Codex can summarize material changes from `.dispatch/` state.
4. Confirm the fallback behavior when no heartbeat is configured.

This workstream validates the runbook and runtime control surfaces. Full
real-repository dogfood with a host heartbeat remains a follow-up because host
wakeup behavior belongs to the Codex app layer, not Dispatch Engine runtime.

## Acceptance

1. Done for runtime: detached runs remain queryable without blocking the
   foreground chat through prior `rfc-0014` validation.
2. Done: status, events, and alerts report pending decisions, blockers,
   protocol violations, failed agents, and material state from JSON state.
3. Done: validation records commands and residual risks.

## Docs-Lane Validation

- `python3 scripts/de.py --help`
- `python3 scripts/de.py status --help`
- `python3 scripts/de.py events --help`
- `python3 scripts/de.py alerts --help`
- `python3 scripts/de.py resolve-decision --help`
- `PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface`
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- Temporary target smoke: import fixture plan, then read `status --json`,
  `events --since event-000001 --json`, and `alerts --json`
- `git diff --check`
- `rg "heartbeat|status --json|events --since|alerts --json|resolve-decision" SKILL.md README.md references specs/rfc-0015-codex-heartbeat-observation`
