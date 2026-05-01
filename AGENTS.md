---
language: en-US
audience: agent
doc_type: router
---

# AGENTS.md

This is the canonical routing file for all coding agents.

Keep this file short. Put detailed rules in `docs/governance/` and use this file to route agents to the right workflow.

## Project Context

Dispatch Engine is a runtime-backed Codex skill for repo-native agent dispatch. The repository root is the installable skill directory, and the bundled runtime lives under `scripts/`.

Optimize governance for a skill-first local CLI/runtime that may grow long-running scheduling behavior, worker adapters, event logs, validation runners, and agent-facing documentation.

Before giving install or copy guidance, verify the skill root contains `SKILL.md`, `agents/openai.yaml`, `scripts/de.py`, `scripts/dispatch_engine/`, and the relevant `references/` files.

## Read Order

1. Read this file first.
2. Read the relevant workflow under `docs/governance/` before acting.
3. If instructions conflict, prefer the more specific workflow file.
4. If a workflow file is missing or stale, update it before relying on it.

## Governance Map

| Situation | Read |
|---|---|
| Any code change | `docs/governance/development-workflow.md` |
| New or changed API, command, config, dependency, adapter, workflow doc, template, or agent entrypoint | `docs/governance/change-gate.md` |
| Code structure, interfaces, dead code, dependencies, or compatibility layers | `docs/governance/code-quality.md` |
| README, docs, examples, generated docs, specs, contributor guidance, or agent instructions | `docs/governance/documentation-standards.md` |
| Skill metadata, bundled runtime packaging, scripts copied into the skill, or install guidance | `SKILL.md`, then `docs/governance/change-gate.md` and `docs/governance/documentation-standards.md` |
| Screenshots, recordings, traces, logs, reports, debug dumps, or scratch files | `docs/governance/temp-artifacts.md` |
| Ambiguous feature or cross-module change | `docs/governance/spec-workflow.md` |
| Creating or revising specs | `docs/governance/spec-production.md` |
| Choosing or reviewing a spec id | `docs/governance/spec-id-policy.md` |
| Spec execution status or parallel workstreams | `docs/governance/spec-execution-status.md` |
| Multi-agent parallel spec implementation | `docs/governance/multi-agent-spec-flow.md` |
| TDD work | `docs/governance/tdd-workflow.md` |
| Validation or test reporting | `docs/governance/validation-workflow.md` |
| PR or review prep | `docs/governance/review-workflow.md` |
| Agent context files | `docs/governance/agent-context.md` |
| Governance file changes | `docs/governance/governance-maintenance.md` |

## Non-Negotiables

- Do not duplicate detailed governance rules in this file or in agent adapter files.
- Thin adapter files such as `CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md` must point here instead of copying rules.
- When adding, deleting, renaming, or moving governance documents, update this file in the same change.
- When changing which workflow applies to a task type, update the Governance Map in this file in the same change.
- New or substantially changed durable docs must declare `language`, `audience`, and `doc_type` near the top.
- Agent-facing docs use English by default unless a local exception is explicit.
- Do not duplicate long-lived documentation; keep one source of truth and route to it.
- Do not skip tests or validation silently. Record what ran and what did not.
- Do not preserve dead code, stale flags, or compatibility paths without an owner and deletion condition.
- Do not scatter temporary artifacts through the repo. Use `.out/` unless local rules say otherwise.
- Do not revert user changes unless explicitly asked.
