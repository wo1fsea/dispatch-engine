---
language: en-US
audience: agent
doc_type: spec
---

# Coordinator Approval Decision Record Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #21 came from alpha-kitchen run `20260505T162914702948Z`. The coordinator
printed or reported approval requirements and exited code 0, but Dispatch
Engine had no `decision.requested` event, no durable `decisions.jsonl` entry,
`pending_decisions: 0`, and no useful alert. The run appeared planned/idle
instead of blocked on a user decision.

Relevant files:

- `references/prompts/coordinator-protocol.md`
- `references/heartbeat-observation.md`
- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/events.py`
- decision helpers/CLI commands under `scripts/dispatch_engine/`
- `tests/test_codex_facing_control_surface.py`
- `tests/test_status_tail.py`

## Change Gate

- Problem: Approval blockers can vanish into stdout/reports.
- Smallest new surface: prompt contract plus status diagnostics for
  approval-required coordinator reports without durable decisions.
- Validation: focused decision/status tests, prompt grep, full unittest
  discovery, and `git diff --check`.

## Proposed Changes

1. Strengthen coordinator prompt:
   - If approval is needed, write a pending decision through the DE decision
     protocol before exiting or waiting.
   - Include decision id, prompt, options when available, eligibility for
     autonomous technical fallback, blocking workstream ids, and evidence.
2. Add/verify runtime status behavior:
   - Pending decisions show in status JSON, alerts, and next actions.
   - Decision records are under `.dispatch/`.
3. Add coordinator completion diagnostics:
   - If a coordinator report says approval/decision required but no durable
     decision exists, surface a material alert/protocol violation.
   - Do not rely on natural-language parsing as the only happy path.
4. Add regression fixture:
   - Coordinator report includes `decisions_required` but no decisions file.
   - Status exposes the mismatch.

## Validation Plan

```bash
rg -n "decision.requested|decisions.jsonl|approval|required|autonomous" references scripts tests specs/rfc-0028-coordinator-approval-decision-record
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

## Risks

- Heuristic report scanning can produce false positives. Prefer explicit
  coordinator decision protocol and keep heuristics conservative.
- Treating missing decisions as hard failures may make recovery noisy. A
  material alert plus blocked next action may be safer unless the run already
  reached a terminal inconsistent state.
