---
language: en-US
audience: agent
doc_type: spec
---

# Review Validator Report Protocol Tech Spec

Product spec: `./PRODUCT.md`

## Change Gate

- Skill-first default: review criteria, validator expectations, skip rules, and acceptance judgment should live in `SKILL.md`, `references/`, and prompt templates.
- Runtime-necessary scope: durable reviewer/validator reports, basic report shape validation, status/tail visibility, and protocol violations.
- Do not add reviewer/validator launchers in this RFC.

## Proposed Changes

- Added `references/review-validator-protocol.md`.
- Added `references/prompts/reviewer-protocol.md`.
- Added `references/prompts/validator-protocol.md`.
- Added centralized reviewer and validator prompt render helpers.
- Added small runtime report writers/validators for reviewer and validator reports.
- Kept `de status` on existing agent counts plus detected protocol violations.

## Workstreams

1. `01-review-validator-guidance`: skill/reference/prompt guidance.
2. `02-report-shape-validation`: minimal report validators and tests.
3. `03-status-docs-validation`: status/docs/spec validation.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
rg "reviewer|validator|review.completed|validation.completed|reports/|reviews/|validation/" README.md SKILL.md references specs/rfc-0009-review-validator-report-protocol
git diff --check
```
