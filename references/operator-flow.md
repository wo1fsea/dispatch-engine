---
language: en-US
audience: agent
doc_type: normative
---

# Operator Flow

Use this reference when interactive Codex is supervising Dispatch Engine.

## Flow

1. Inspect the target repository.
2. Summarize discovered instructions, planning sources, and validation hints.
3. Plan the objective before dispatching workers.
4. Ask the user before high-risk execution, parallel work, or unresolved decisions.
5. Start or resume the runtime loop.
6. Monitor status and event logs.
7. Resolve decisions explicitly.
8. Report validation evidence and residual risk.

## Guardrail

Interactive Codex operates Dispatch Engine through CLI commands and files. It should not rely on private chat runtime internals as durable orchestration state.
