---
workstream_id: 01-implementation
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - scripts/dispatch_engine/plan_schema.py
  - references/prompts/coordinator-protocol.md
  - references/worker-protocol.md
  - references/decision-blocker-protocol.md
  - tests/test_plan_schema_init.py
  - tests/test_agent_capability_profiles.py
  - specs/rfc-0031-issue-evidence-capability-preflight/
depends_on: []
updated: 2026-05-06
---

# Workstream 01: Issue Evidence Capability Preflight

Add warning-only diagnostics and guidance for GitHub issue evidence workstreams
whose capability profile denies network access.

Validation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_plan_schema_init
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
git diff --check
```
