---
language: en-US
audience: agent
doc_type: normative
---

# Spec Workflow

## When To Write A Spec

Write a spec before implementation when at least one is true:

- Behavior is ambiguous or user-visible.
- The change spans multiple modules or ownership boundaries.
- The change affects persistence, permissions, security, billing, migration, or public APIs.
- A coding agent needs stable product intent before implementation.
- Reviewers need to approve direction before code churn begins.

Skip specs for narrow bug fixes, mechanical refactors, dependency bumps, or obvious single-file changes.

## Required Files

```text
specs/<spec-id>/
  PRODUCT.md
  TECH.md
  STATUS.md
  workstreams/
    01-implementation.md
```

`PRODUCT.md` describes user/API-visible behavior as testable invariants.

`TECH.md` describes current code context, proposed changes, validation, risks, and follow-ups.

Use `docs/governance/spec-production.md` when creating or revising spec files.

## Keep Specs Current

If implementation changes user-visible behavior, update `PRODUCT.md`.

If implementation changes module boundaries, sequencing, validation, or risks, update `TECH.md`.

Use `docs/governance/spec-execution-status.md` to manage not-started, partial, blocked, ready-review, and completed execution states.

Use `docs/governance/multi-agent-spec-flow.md` when multiple agents or branches implement the same spec in parallel.
