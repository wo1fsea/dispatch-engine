---
language: en-US
audience: agent
doc_type: spec
---

# Issue Evidence Capability Preflight Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #26 came from dogfood run `20260505T182233983007Z`. Workstream
`06-integration-validation-and-issue-evidence` needed evidence for GitHub
issues #20-#24 but had `network_access: none`. The worker ran read-only
`gh issue view` commands anyway, which was recorded as capability overreach.

Current code has validation-command network warnings, but it does not detect
issue-evidence intent in workstream scope/title/validation before dispatch.

Relevant files:

- `scripts/dispatch_engine/plan_schema.py`
- `references/prompts/coordinator-protocol.md`
- `references/worker-protocol.md`
- `references/decision-blocker-protocol.md`
- `tests/test_plan_schema_init.py`
- `tests/test_agent_capability_profiles.py`

## Change Gate

- Problem: issue-evidence tasks can conflict with denied network capability.
- Smallest new surface: warning-only plan diagnostic plus coordinator guidance.
- Do not auto-escalate capabilities from runtime heuristics.

## Proposed Changes

1. Extend plan diagnostics:
   - inspect title/scope/validation strings for GitHub issue evidence phrases;
   - if `network_access` is `none`, attach a warning such as
     `issue_evidence_requires_network_access`.
2. Update coordinator protocol:
   - treat this warning as pre-dispatch work;
   - record a pending decision or local-only evidence note before worker spawn.
3. Update worker guidance:
   - workers must not run `gh issue view` unless the capability profile or
     decision grants it;
   - local-only evidence mode must be explicit in the report.
4. Add tests for warning generation and prompt coverage.

## Validation Plan

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_plan_schema_init
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
rg -n "issue_evidence_requires_network_access|local-only evidence|gh issue view" references scripts tests specs/rfc-0031-issue-evidence-capability-preflight
git diff --check
```

## Risks

- Heuristics can false-positive on docs that merely mention issues. Keep the
  diagnostic warning-only and let the coordinator/user decide.
