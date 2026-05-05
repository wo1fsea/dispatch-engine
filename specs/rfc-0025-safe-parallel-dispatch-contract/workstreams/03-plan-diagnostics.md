---
workstream_id: 03-plan-diagnostics
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - scripts/dispatch_engine/plan_schema.py
  - scripts/dispatch_engine/cli.py
  - tests/
  - specs/rfc-0025-safe-parallel-dispatch-contract/
depends_on:
  - 01-parallelism-contract
updated: 2026-05-06
---

# Workstream 03: Plan Diagnostics

Add warning-only runtime diagnostics only if implementation review decides
skill/prompt guidance is not enough.

Candidate diagnostics:

- all workstreams are serial with no serial rationale;
- long dependency chain with repeated broad write scopes;
- independent workstreams lack `parallel_group`;
- broad directory write roots are used despite concrete file lists;
- coordinated overlap lacks owner, integration, and validation protocol.

Constraints:

- Diagnostics are advisory by default.
- Do not add a deterministic scheduler.
- Do not reject conservative plans unless existing overlap validation already
  rejects them.

Validation if runtime code changes:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_plan_schema
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py init --help
git diff --check
```
