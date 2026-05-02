---
language: en-US
audience: agent
doc_type: spec
---

# Workstream Acceptance Guidance Tech Spec

## Proposed Changes

- Add `references/workstream-acceptance-guidance.md` for workstream state
  meanings, evidence paths, and acceptance/change/blocker semantics.
- Add a reusable prompt addendum for acceptance calls.
- Keep reviewer and validator prompts aligned with the acceptance vocabulary.
- Rely on existing `de status` workstream counts and existing mechanical report
  violations unless a missing evidence gap is proven.
- Do not add a scheduler, transition engine, or acceptance engine.

## Workstreams

1. `01-state-guidance`: reference and prompt guidance.
2. `02-status-evidence-checks`: minimal status/violation tests if needed.
3. `03-docs-validation`: docs and validation.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg "accepted|needs-fix|reviewing|validating|blocked|workstream" references specs/rfc-0010-workstream-acceptance-guidance
git diff --check
```
