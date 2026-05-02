---
language: en-US
audience: agent
doc_type: fixture
---

# Dogfood Runbook Fixture

This directory contains the minimal plan fixture used by
`references/dogfood-runbook.md` and
`tests/test_dogfood_runbook_fixture.py`.

The fixture is intentionally small:

- `plan.json` imports into a target repository with `de init`.
- Runtime-generated files belong under the target repository's `.dispatch/`.
- The fixture itself is static project content and should not be copied into
  `.dispatch/` by tests or operators.

Smoke command:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dogfood_runbook_fixture
```
