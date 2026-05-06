---
language: en-US
audience: agent
doc_type: spec
---

# Validator Artifact Evidence Gate Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #27 came from Alpha Kitchen run `20260505T175620476602Z`, where
`validator-003` completed with `passed` but its validator report missed
`artifacts`. Current runtime diagnostics can detect missing validator evidence,
but the issue remains open because the acceptance/gating behavior and repair
path need to be explicit.

Relevant files:

- `references/review-validator-protocol.md`
- `references/prompts/validator-protocol.md`
- `references/prompts/reviewer-validator-protocol.md`
- `references/prompts/coordinator-protocol.md`
- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/dashboard.py`
- `tests/test_review_validator_protocol.py`
- `tests/test_status_tail.py`
- `tests/test_dashboard_observer.py`

## Change Gate

- Problem: malformed validator evidence can look like pass evidence during
  coordinator reporting.
- Smallest new surface: enforce current diagnostics as acceptance guidance and
  add regression coverage for pass-without-artifacts.
- Do not mutate old reports automatically.

## Proposed Changes

1. Confirm/report validator schema diagnostics:
   - missing or empty `artifacts` on non-skipped reports is
     `missing_validation_evidence`;
   - next action suggests repair with exact fields.
2. Strengthen coordinator/validator prompts:
   - validator `passed` requires artifact references;
   - coordinator cannot accept malformed validator evidence as clean.
3. Add dashboard/status regression:
   - validator detail shows missing artifacts and repair action;
   - alerts stay visible until repaired or resolved.
4. Add/adjust fixtures for `validator-003` style reports.

## Validation Plan

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
rg -n "artifacts|missing_validation_evidence|validator report" references scripts tests specs/rfc-0032-validator-artifact-evidence-gate
git diff --check
```

## Risks

- Some old dogfood runs may remain dirty; fix by repair or explicit protocol
  resolution, not by weakening the validator schema.
