---
language: en-US
audience: mixed
doc_type: spec
---

# Skill-First Packaging Product Spec

## Summary

Reorganize Dispatch Engine as a runtime-backed Codex skill whose repository root is directly installable as a skill directory.

## Goals / Non-goals

- Goal: Make the repository root contain the required skill entrypoint and metadata.
- Goal: Bundle a runnable local runtime under `scripts/` so copying or cloning the repository as a skill includes the execution program.
- Goal: Keep GitHub-facing README and engineering governance available for maintainers.
- Non-goal: Implement full agent dispatch, review loops, or safe parallel execution in this change.
- Non-goal: Split runtime and skill into separate repositories.

## Behavior

1. When the repo is copied or cloned into a Codex skills directory, Codex can discover `SKILL.md`.
2. When an operator uses the skill, `SKILL.md` points to the bundled runtime entrypoint under `scripts/de.py`.
3. When a maintainer changes runtime packaging, the skill packaging rule reminds them to keep the bundled runtime present before install guidance.
4. When an operator runs smoke checks, `python scripts/de.py --help` and `python scripts/de.py version` succeed.
5. When an operator needs deeper protocol details, the skill routes them to one-level `references/` files.

## Open Questions

- Should the CLI eventually be installed as `de` through `pipx`, or stay script-invoked from the skill path?
- Should generated run state under `.dispatch/` be ignored by default in this repository?
