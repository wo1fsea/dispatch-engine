---
language: en-US
audience: agent
doc_type: spec
---

# Initial Governance Tech Spec

Product spec: `./PRODUCT.md`

## Context

Dispatch Engine is a new public repository with an initial README and no implementation code yet. The repo is expected to grow into a local CLI/runtime with worker adapters, review loops, validation handling, event logs, and companion skill/operator documentation.

Because the repo will be operated by agents, it needs a short canonical router plus detailed governance modules. The governance should stay lightweight for narrow changes but strict around public CLI surface, runtime state formats, event protocols, adapters, validation behavior, and agent instructions.

## Proposed Changes

- Add `AGENTS.md` as the canonical agent router.
- Add thin adapters for Claude, Gemini, and GitHub Copilot.
- Add detailed governance workflows under `docs/governance/`.
- Add starter spec infrastructure under `specs/`.
- Add `.out/` to `.gitignore` for temporary artifacts.
- Add a pull request template that asks for spec, change-gate, validation, documentation, and review evidence.
- Update root README to route contributors and agents to `AGENTS.md`.

## Testing and Validation

- Confirm generated governance paths exist.
- Confirm `AGENTS.md` routes to the detailed workflow files.
- Confirm thin adapters do not duplicate detailed governance rules.
- Confirm starter spec files have concrete content and dates rather than placeholder-only templates.
- Confirm `git status --short` shows only intentional governance additions and README updates.

## Risks and Follow-ups

- Risk: Governance could become heavier than the early repo needs. Mitigation: `AGENTS.md` and governance docs explicitly allow direct changes for narrow mechanical work.
- Risk: Runtime and companion skill boundaries may change. Mitigation: keep current guidance descriptive and update it when packaging decisions become stable.
- Follow-up: Once the runtime language is chosen, add canonical setup, test, lint, typecheck, and smoke commands.
- Follow-up: Create a real product/runtime spec before implementing multi-step scheduling or worker execution.
