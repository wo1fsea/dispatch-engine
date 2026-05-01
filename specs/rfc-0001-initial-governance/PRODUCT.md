---
language: en-US
audience: mixed
doc_type: spec
---

# Initial Governance Product Spec

## Summary

Initialize lightweight repository governance so humans and agents can safely evolve Dispatch Engine as a runtime-backed skill.

## Goals / Non-goals

- Goal: Provide a canonical agent router and detailed governance workflows for skill packaging, development, validation, review, documentation, specs, temporary artifacts, and multi-agent work.
- Goal: Keep repo instructions discoverable for Codex, Claude, Gemini, GitHub Copilot, and future agent operators.
- Goal: Establish a starter spec/status structure for future ambiguous or cross-module work.
- Non-goal: Force every change through a heavy spec process.
- Non-goal: Define Dispatch Engine's runtime architecture in this initial governance spec.
- Non-goal: Replace the repository README as the public product introduction.

## Behavior

1. When an agent starts work in this repo, it can read `AGENTS.md` and find the relevant workflow without searching through unrelated files.
2. When an agent or human changes governance docs, they update the router or adapter files in the same change when routing changes.
3. When a change adds CLI, config, adapter, event, file-format, workflow, or agent-entrypoint surface, the change gate provides a repeatable decision checklist.
4. When a change affects behavior, docs, validation, or review expectations, the repo has a canonical place to record evidence.
5. Narrow mechanical changes can still proceed directly when a spec would add ceremony without reducing risk.

## Open Questions

- Which implementation language and package manager will become canonical for the runtime?
- Will the bundled runtime remain script-invoked from the skill path, or later gain a separate `pipx` or package install path?
- Should `.dispatch/` run state be ignored, committed selectively, or controlled per target repository?
