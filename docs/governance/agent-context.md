---
language: en-US
audience: agent
doc_type: normative
---

# Agent Context

## Canonical Rule

`AGENTS.md` is the canonical routing file for all coding agents.

## Project Context

Dispatch Engine is a local orchestration runtime. Agents should expect work around CLI design, file-based or database-backed runtime state, scheduling rules, worker/reviewer adapters, validation commands, event logs, and companion skill/operator documentation.

Do not assume a universal external spec format. The product direction is to adapt to a target repository's own planning conventions and keep Dispatch Engine's normalized execution model internal.

## Thin Adapters

- `CLAUDE.md` imports `AGENTS.md`.
- `GEMINI.md` imports `AGENTS.md`.
- `.github/copilot-instructions.md` points to `AGENTS.md`.

Adapter files must not duplicate detailed workflow rules. Add tool-specific notes only when the tool truly requires them.

## Maintenance

When an adapter is added, removed, renamed, or moved, update this file and `AGENTS.md` in the same change.
