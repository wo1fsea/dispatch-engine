---
language: en-US
audience: mixed
doc_type: spec
---

# Review Validator Report Protocol Product Spec

## Summary

Worker reports are implementation evidence, not acceptance evidence. Dispatch Engine needs a skill-first protocol for reviewer and validator evidence so a workstream can move from "implemented" to "accepted" without pretending that code edits alone are completion.

This spec defines reviewer and validator report shapes, prompt guidance, status visibility, and conservative protocol violations. Runtime code is allowed only where durable reports, status/tail visibility, or mechanical validation are necessary.

## Goals / Non-goals

- Goal: Define reviewer and validator report contracts under `.dispatch/runs/<run-id>/reports/`, `reviews/`, or `validation/`.
- Goal: Add skill/reference/prompt guidance for when review and validation are required.
- Goal: Make `de status` able to distinguish worker implementation evidence from review/validation evidence.
- Goal: Require reviewer/validator registration before their reports are accepted.
- Goal: Add conservative protocol violations for missing or malformed review/validation evidence.
- Non-goal: Launch reviewer or validator provider processes.
- Non-goal: Build a full acceptance state machine; that belongs to rfc-0010.
- Non-goal: Replace human judgment with runtime approval logic.

## Behavior Invariants

1. A worker report alone does not make a workstream accepted.
2. Reviewer and validator behavior is described in skill/reference/prompt guidance first.
3. Runtime helpers may validate report shape and expose report status.
4. Reviewer reports include status, findings, risks, requested changes, and recommendation.
5. Validator reports include command, status, output summary, artifacts, and not-run reasons.
6. Workstream acceptance requires review/validation evidence or an explicit recorded reason for skipping it.

## Decisions

- Reviewer reports live in `.dispatch/runs/<run-id>/reviews/<agent-id>.json`.
- Validator reports live in `.dispatch/runs/<run-id>/validation/<agent-id>.json`.
- Validator reports store command evidence as a summary plus artifact references.
- Skipped validation is represented as `status: "skipped"` with `not_run_reason`.
- Acceptance judgment remains skill-first. Runtime only checks mechanical report shape, status values, path placement, and evidence presence.
