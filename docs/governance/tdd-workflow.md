---
language: en-US
audience: agent
doc_type: normative
---

# TDD Workflow

TDD evidence is expected for behavior changes.

## Loop

TDD is the inner loop inside the broader `Plan -> Develop -> Verify -> Fix` engineering cycle in `development-workflow.md`.

```text
Product behavior -> test plan -> red -> green -> refactor -> broaden -> validate -> record
```

## Steps

1. Write or update behavior invariants in `PRODUCT.md`.
2. Map important invariants to tests in `TECH.md`.
3. Add the smallest failing test that proves the behavior is not implemented.
4. Run the narrow test command and record the red result.
5. Implement the smallest change that makes the test pass.
6. Run the same narrow command and record the green result.
7. Refactor only while tests are green.
8. Broaden validation to relevant unit, integration, e2e, or manual checks.
9. Record commands run, checks skipped, and residual risk in the PR or implementation log.

## PR Evidence

```markdown
## TDD Evidence

- Red:
- Green:
- Broader validation:
- Tests not run:
```
