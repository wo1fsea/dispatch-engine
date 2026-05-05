---
language: en-US
audience: mixed
doc_type: spec
---

# Coordinator Approval Decision Record Product Spec

## Summary

When a coordinator needs human approval, it must record a durable pending
decision before exiting or waiting. A successful coordinator process must never
hide an approval blocker by printing a question only to stdout or a report.

This spec covers GitHub issue #21.

## Goals / Non-goals

- Goal: Convert coordinator approval prompts into durable
  `decision.requested` events and `decisions.jsonl` records.
- Goal: Make status, alerts, heartbeat checks, and dashboard surfaces show a
  pending user decision whenever implementation is blocked on approval.
- Goal: Treat "approval required but no pending decision recorded" as a
  protocol violation or failed/incomplete coordinator outcome.
- Goal: Preserve the four-heartbeat autonomous technical fallback only for
  eligible technical decisions that were recorded durably.
- Non-goal: Let Dispatch Engine answer product or policy decisions
  automatically.
- Non-goal: Require runtime to understand every natural-language question from
  stdout.

## Behavior Invariants

1. Coordinator approval requests are durable records, not stdout-only text.
2. A coordinator that exits code 0 after asking for approval without recording a
   pending decision has violated the protocol.
3. `de status --json` includes pending decision counts and next actions for
   recorded decisions.
4. Heartbeat instructions act only on durable decisions and count unanswered
   checks against the decision id.
5. Coordinator reports may summarize decisions, but the report is not the
   source of truth.

## User Experience

- The user sees a clear pending decision in heartbeat summaries and dashboard
  state.
- Interactive Codex can resolve eligible technical decisions with
  `de resolve-decision --autonomous-technical` after the documented threshold.
- A blocked run does not appear idle or successfully finished.

## Open Questions

- Should missing decision records mark the run failed immediately, or keep the
  run blocked with a material alert until the operator cancels or resumes?
- Should approval-required phrases in coordinator reports be linted
  heuristically as a best-effort diagnostic?
