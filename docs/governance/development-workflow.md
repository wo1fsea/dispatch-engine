---
language: en-US
audience: agent
doc_type: normative
---

# Development Workflow

## Outer Loop

Use this loop for all non-trivial engineering work:

```text
Plan -> Develop -> Verify -> Fix
```

1. Plan: read the relevant governance docs, decide whether a spec is needed, identify risk, and choose the smallest coherent task shape.
2. Develop: make the change. When TDD applies, use `docs/governance/tdd-workflow.md` inside this phase.
3. Verify: run narrow validation first, broaden when behavior or shared contracts changed, and record evidence. When TDD applies, the broaden/validate/record steps come from `docs/governance/tdd-workflow.md`.
4. Fix: respond to failing tests, review feedback, or validation gaps. If reality changed, update specs or governance docs before repeating Develop/Verify.

TDD is not a competing workflow. It is the inner loop used inside Develop and Verify when behavior changes call for it.

## Default Steps

1. Read `AGENTS.md`.
2. Read the workflow file that matches the task.
3. Inspect the existing code and tests before editing.
4. If adding or expanding project surface, apply `docs/governance/change-gate.md`.
5. For code changes, apply `docs/governance/code-quality.md`.
6. For docs, examples, generated docs, specs, contributor guidance, or agent instructions, apply `docs/governance/documentation-standards.md`.
7. If producing temporary artifacts, apply `docs/governance/temp-artifacts.md`.
8. Make the smallest coherent change.
9. Run the narrowest meaningful validation first.
10. Broaden validation when behavior, contracts, docs, or shared modules changed.
11. Record tests run, docs checked, tests skipped, and residual risk.

## Direct Implementation

Use direct implementation for narrow bug fixes, mechanical refactors, dependency bumps, documentation-only changes, or obvious single-file changes.

## Spec-Driven Implementation

Use `docs/governance/spec-workflow.md` when behavior is ambiguous, user-visible, cross-module, or high risk.
