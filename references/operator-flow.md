---
language: en-US
audience: agent
doc_type: normative
---

# Operator Flow

Use this reference when interactive Codex is supervising Dispatch Engine.

## Boundary

Interactive Codex plus the skill owns repository discovery, planning judgment, workstream splitting, review, validation strategy, and user conversation. Dispatch Engine runtime owns explicit plan import, durable `.dispatch/` state, status/tail, event logs, and the future mechanical orchestrator loop.

Dispatch Engine-generated non-project runtime content must live under `.dispatch/` in the target repository. Accepted project work stays in the target repository's normal project paths.

## Flow

1. Read the target repository's local instructions, governance, source layout, tests, docs, and the user's objective from interactive Codex.
2. Summarize the planning basis: relevant repo rules, workstream boundaries, dependencies, write scopes, validation strategy, risks, and unresolved decisions.
3. Create an explicit dispatch plan from that Codex-owned context.
4. Store any Dispatch Engine-generated plan file under `.dispatch/plans/`.
5. Import the explicit plan into `.dispatch/runs/<run-id>/` with `python3 scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json`.
6. Ask the user before high-risk execution, parallel work, or unresolved decisions.
7. Start or resume the future runtime loop from imported plan state.
8. Monitor status and event logs through `status`, `tail`, and `.dispatch/runs/` files.
9. Resolve decisions explicitly.
10. Report validation evidence and residual risk.

## Future Runtime Loop

The future loop is imported plan -> scheduler -> workers -> reviewer -> validation -> status/tail. User interaction remains outside the runtime in interactive Codex, which can keep talking with the user while polling status and tail output.

See `references/orchestrator-loop.md` for the adapter-neutral design.

## Guardrail

Interactive Codex operates Dispatch Engine through CLI commands and files. It should not rely on private chat runtime internals as durable orchestration state, and the runtime should not infer repository conventions from broad scans when an explicit plan is required.
