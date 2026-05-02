---
language: en-US
audience: agent
doc_type: spec
---

# Dogfood Runbook Fixture Tech Spec

## Proposed Changes

- Add a dogfood runbook under `docs/` or `references/`.
- Add a sample dispatch plan fixture.
- Add fake coordinator/worker fixture scripts only if useful for repeatable smoke tests.
- Add e2e smoke tests only where they remain deterministic and do not invoke real providers.

## Workstreams

1. `01-runbook-and-plan-fixture`: docs and sample plan.
2. `02-fake-provider-fixture`: fake-provider scripts/tests.
3. `03-e2e-validation-docs`: smoke validation and docs.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
git diff --check
```
