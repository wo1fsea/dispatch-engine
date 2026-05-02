---
language: en-US
audience: mixed
doc_type: spec
---

# Workstream Acceptance Guidance Product Spec

## Summary

Dispatch Engine needs a shared vocabulary for workstream progress, but most transition judgment should remain skill-first. This spec defines guidance and minimal runtime-visible state for planned -> implemented -> reviewed -> validated -> accepted/blocked/failed.

## Goals / Non-goals

- Goal: Define workstream state meanings and acceptance criteria.
- Goal: Document legal transitions as guidance for coordinators/reviewers.
- Goal: Expose workstream progress clearly in `de status`.
- Goal: Detect obvious contradictions such as accepted workstreams with no evidence.
- Non-goal: Build a heavy runtime transition engine.
- Non-goal: Automate acceptance judgment.

## Candidate States

`planned`, `assigned`, `implementing`, `implemented`, `reviewing`, `needs-fix`, `validating`, `accepted`, `blocked`, `failed`.

## Skill-first Gate

State meaning, transition judgment, and fix-loop guidance live in skill/reference docs first. Runtime should only read state, summarize it, and detect obvious missing evidence.

## Acceptance Evidence

The normative guidance is `references/workstream-acceptance-guidance.md`.
Acceptance combines worker reports, reviewer reviews, validator validation, and
decision/blocker records. Reviewer acceptance and validator success are evidence
inputs, not an automated final state transition.
