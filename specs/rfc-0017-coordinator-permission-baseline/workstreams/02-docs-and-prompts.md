---
language: en-US
audience: agent
doc_type: workstream
---

# Docs And Prompts

## Scope

Record the permission baseline in skill documentation, reference protocols, and
centralized prompt templates.

## Tasks

- Update `SKILL.md` and `README.md`.
- Update operator, event, orchestrator, and worker references.
- Update coordinator and worker prompt templates.
- Record validation evidence in `STATUS.md`.

## Validation

```bash
rg -n "danger-full-access|bypassPermissions|worker permission scope|high provider permissions" SKILL.md README.md references specs/rfc-0017-coordinator-permission-baseline
git diff --check
```
