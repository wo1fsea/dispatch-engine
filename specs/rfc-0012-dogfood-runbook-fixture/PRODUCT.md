---
language: en-US
audience: mixed
doc_type: spec
---

# Dogfood Runbook Fixture Product Spec

## Summary

Before real users can try Dispatch Engine, the project needs a repeatable dogfood scenario that proves the skill-first coordinator flow can produce durable `.dispatch/` evidence from init through status/tail and final summary.

## Goals / Non-goals

- Goal: Provide a fake-provider dogfood fixture that does not call real Codex or Claude.
- Goal: Provide an operator runbook for a small self-task.
- Goal: Verify init -> run -> registered workers -> reports -> review/validation evidence -> status/tail.
- Non-goal: Prove real provider quality.
- Non-goal: Build a dashboard.

## Skill-first Gate

The dogfood procedure belongs mainly in docs/runbooks and fixture scripts. Runtime changes are allowed only to fix missing durable state or status visibility discovered by dogfood.
