---
spec_id: rfc-0012-dogfood-runbook-fixture
language: en-US
audience: agent
doc_type: spec
status: validated
implementation: completed
validation: passed
coordinator: dispatch-engine
updated: 2026-05-02
---

# Status

## Summary

Validated. This spec now provides a minimal deterministic dogfood path with a
static plan fixture, operator runbook, and smoke test that imports the fixture,
renders coordinator dry-run, launches live-form coordinator state through a fake
provider shim, registers worker/reviewer/validator evidence, queries
status/tail, and records decision/blocker lifecycle records.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Runbook and plan fixture | validated | dispatch-engine | main | rfc-0011 | 2026-05-02 |
| 02 | Fake-provider fixture | validated | dispatch-engine | main | 01 | 2026-05-02 |
| 03 | E2E validation docs | validated | dispatch-engine | main | 01, 02 | 2026-05-02 |

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dogfood_runbook_fixture
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
git diff --check
```

Result on 2026-05-02: all commands passed.
