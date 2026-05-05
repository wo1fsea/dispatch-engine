---
workstream_id: 04-docs-dogfood-validation
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - README.md
  - specs/README.md
  - specs/rfc-0025-safe-parallel-dispatch-contract/
  - .dispatch/plans/
depends_on:
  - 02-coordinator-ready-set
  - 03-plan-diagnostics
updated: 2026-05-06
---

# Workstream 04: Docs And Dogfood Validation

Finish documentation and prove the corrected behavior with a small dogfood
fixture or real run.

Required behavior:

- Update `specs/README.md`.
- Add or document a dogfood plan with at least two independent, disjoint
  workstreams.
- Validate that coordinator output records a parallel dispatch batch, or a
  concrete reason why parallel dispatch was not possible.
- Record final validation and move `STATUS.md` forward only after evidence
  exists.

Validation:

```bash
rg -n "rfc-0025-safe-parallel-dispatch-contract|parallel dispatch|serial rationale" specs README.md references
python3 scripts/de.py run . --dry-run
git diff --check
```
