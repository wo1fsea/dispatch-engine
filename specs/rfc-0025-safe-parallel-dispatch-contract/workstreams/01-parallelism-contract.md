---
workstream_id: 01-parallelism-contract
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - SKILL.md
  - README.md
  - references/operator-flow.md
  - references/operator-guide.md
  - references/orchestrator-loop.md
  - specs/rfc-0025-safe-parallel-dispatch-contract/
depends_on: []
updated: 2026-05-06
---

# Workstream 01: Parallelism Contract

Update skill and operator guidance so interactive Codex must perform explicit
parallelism analysis before writing a dispatch plan.

Required behavior:

- Describe safe batches, dependency rationale, write-scope conflicts,
  integration gates, and concurrency budget.
- Prefer disjoint assigned files over broad shared write roots.
- Require serial rationale for workstreams that appear ready but are held back.
- Keep small one-workstream plans lightweight by allowing "parallelism not
  applicable."

Validation:

```bash
rg -n "parallelism|concurrency budget|serial rationale|parallel_group|shared-write-approved" SKILL.md README.md references specs/rfc-0025-safe-parallel-dispatch-contract
git diff --check
```
