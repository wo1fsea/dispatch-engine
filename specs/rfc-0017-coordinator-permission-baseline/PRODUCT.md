---
language: en-US
audience: mixed
doc_type: spec
---

# Coordinator Permission Baseline Product Spec

## Summary

Dispatch Engine should launch the provider CLI coordinator with high provider
permissions by default, while keeping the coordinator-only boundary intact.
The coordinator needs enough capability to spawn provider-native workers,
install dependencies, inspect repository state, and run validation. Actual
project implementation still belongs to registered workers, reviewers, or
validators, and the coordinator decides their permission scope per assignment.

## Goals / Non-goals

- Goal: Make Codex the default provider with `codex exec --sandbox danger-full-access`.
- Goal: Make Claude use its bypass-permissions coordinator launch shape.
- Goal: Keep worker, reviewer, and validator permission scope delegated to the coordinator.
- Goal: Preserve the rule that coordinators write Dispatch Engine runtime state under `.dispatch/` and do not directly implement project-file changes.
- Goal: Surface the exact coordinator launch argv in `de run --dry-run`.
- Non-goal: Add a first-class Dispatch Engine worker process launcher.
- Non-goal: Hard-code worker sandbox flags in Dispatch Engine runtime.
- Non-goal: Remove assigned file and allowed write root validation.

## Behavior Invariants

1. Omitted `--provider` uses provider `codex`.
2. Codex coordinator argv includes `--sandbox danger-full-access`.
3. Claude coordinator argv includes `--dangerously-skip-permissions` and `--permission-mode bypassPermissions`.
4. Dry-run output renders the same provider permission flags as live execution.
5. A coordinator remains coordinator-only even when launched with high provider permissions.
6. Worker permission scope is assigned by the coordinator through assigned files, allowed write roots, validation expectations, and provider-native launch options.
7. Dispatch Engine report validation still rejects worker changed files outside assigned files and allowed write roots.

## Acceptance

- Unit tests assert default Codex dry-run and live-launch command shapes include `--sandbox danger-full-access`.
- Unit tests assert explicit Claude dry-run and live-launch command shapes include bypass permissions.
- Skill, README, reference protocols, and prompt templates describe the coordinator high-permission baseline and worker delegated permission scope.
