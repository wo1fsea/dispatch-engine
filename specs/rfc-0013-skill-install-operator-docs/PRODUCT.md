---
language: en-US
audience: mixed
doc_type: spec
---

# Skill Install Operator Docs Product Spec

## Summary

The first usable version needs install and operator documentation that explains how to copy/clone the skill, initialize a target repo, run a coordinator, inspect status, and understand `.dispatch/` state.

## Goals / Non-goals

- Goal: Document skill installation and smoke checks.
- Goal: Document target repo operator flow.
- Goal: Document `.dispatch/` commit/ignore guidance.
- Goal: Document failure recovery and known limits.
- Non-goal: Publish package installers.
- Non-goal: Build a UI.

## Skill-first Gate

This spec should be almost entirely docs and skill guidance. Runtime changes are out of scope unless docs uncover a broken smoke command.
