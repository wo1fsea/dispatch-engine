---
language: en-US
audience: agent
doc_type: normative
---

# Agent Context

## Canonical Rule

`AGENTS.md` is the canonical routing file for all coding agents.

## Project Context

Dispatch Engine is a runtime-backed Codex skill. The repository root is the installable skill directory, and the bundled runtime lives under `scripts/`.

Agents should expect work around `SKILL.md`, `agents/openai.yaml`, bundled runtime scripts, CLI design, file-based or database-backed runtime state, scheduling rules, worker/reviewer adapters, validation commands, event logs, and operator documentation.

Do not assume a universal external spec format. The product direction is to adapt to a target repository's own planning conventions and keep Dispatch Engine's normalized execution model internal.

Before telling a user to install or copy the skill, confirm the runtime program is present inside the skill directory and smoke-tested.

## Thin Adapters

- `CLAUDE.md` imports `AGENTS.md`.
- `GEMINI.md` imports `AGENTS.md`.
- `.github/copilot-instructions.md` points to `AGENTS.md`.

Adapter files must not duplicate detailed workflow rules. Add tool-specific notes only when the tool truly requires them.

## Maintenance

When an adapter is added, removed, renamed, or moved, update this file and `AGENTS.md` in the same change.
