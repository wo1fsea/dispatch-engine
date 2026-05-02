---
language: en-US
audience: agent
doc_type: workstream
status: validated
updated: 2026-05-02
---

# 01 - Spec And Guidance Baseline

## Scope

Record the corrected observation boundary in durable project material:

- `de` CLI is Codex-facing, JSON-first, and scriptable.
- Human interaction remains in interactive Codex.
- Detached runs do not automatically wake the foreground chat.
- Host heartbeat automation is the preferred wakeup mechanism when available.
- Without heartbeat, Codex reads latest status on the next user message.

## Acceptance

1. `PRODUCT.md` and `TECH.md` describe the observation model.
2. `SKILL.md` tells interactive Codex how to explain detached monitoring
   honestly.
3. `references/operator-flow.md` names heartbeat as a host-layer mechanism.
4. `specs/README.md` indexes the new spec.
5. Vault notes record the decision and next implementation direction.

## Validation

- `python3 scripts/de.py --help`
- `python3 scripts/de.py status --help`
- `git diff --check`
