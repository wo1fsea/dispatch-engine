---
spec_id: rfc-0016-autonomous-decision-records
language: en-US
audience: agent
doc_type: spec
status: planned
created: 2026-05-03
---

# Autonomous Decision Records Product Spec

## Problem

Detached Dispatch Engine runs can be supervised by a host heartbeat while the
human user is away. The heartbeat rule allows interactive Codex to resolve the
same pending technical decision after four unanswered checks, but the current
record only stores free-form resolution text and actor.

That is enough to continue a run, but not enough to audit why the decision was
eligible, how many unanswered heartbeat checks occurred, which categories were
excluded, or what validation was expected after the choice.

## Goal

Make autonomous technical decisions durable, queryable, and mechanically
recognizable under `.dispatch/` without moving the choice-making judgment into
Dispatch Engine runtime.

Runtime should store a structured record when outer Codex has already decided
that the four-heartbeat fallback applies. Status output should make those
choices easy to summarize at final completion.

## Non-Goals

- Dispatch Engine runtime does not decide whether a pending decision is
  technical.
- Dispatch Engine runtime does not pick the option.
- Dispatch Engine runtime does not create, own, or schedule Codex host
  heartbeats.
- Dispatch Engine runtime does not bypass unresolved product, security,
  privacy, deployment, credential, destructive data, legal, financial, or
  business-scope decisions.

## User Experience

When heartbeat observation reaches four unanswered checks for an eligible
technical decision, outer Codex can resolve it through the existing
`resolve-decision` surface with autonomous metadata:

```bash
python3 scripts/de.py resolve-decision <repo> \
  --id decision-001 \
  --option minimal_adapter \
  --autonomous-technical \
  --unanswered-heartbeats 4 \
  --autonomous-rationale "Minimal adapter keeps existing contracts and is reversible." \
  --validation-expected "PYTHONPATH=scripts python3 -m unittest discover -s tests" \
  --json
```

The latest decision record then carries:

- `resolution_mode: autonomous_technical`
- `resolved_by: interactive-codex-autonomous`
- selected option id
- `autonomous_decision` eligibility metadata
- validation expectations for the work that follows

`status --json` should include an `autonomous_decisions` summary so final
reports can list every autonomous choice.

## Acceptance Criteria

- Autonomous technical decision resolutions are append-only entries in
  `.dispatch/runs/<run-id>/decisions.jsonl`.
- The runtime rejects autonomous resolutions with fewer than four unanswered
  heartbeat checks or missing rationale.
- `resolve-decision --autonomous-technical` defaults actor to
  `interactive-codex-autonomous`.
- `status --json` exposes a count and records for resolved autonomous technical
  decisions.
- Decision/blocker and heartbeat docs describe the structured record and the
  boundary between outer Codex judgment and runtime persistence.
