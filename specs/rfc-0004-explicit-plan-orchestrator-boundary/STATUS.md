---
spec_id: rfc-0004-explicit-plan-orchestrator-boundary
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
coordinator: codex
updated: 2026-05-02
---

# Status

## Summary

Ready for review. All workstreams are validated. This spec corrects the Dispatch Engine architecture by moving repository discovery, planning judgment, and workstream splitting back to interactive Codex plus the skill, while keeping the runtime responsible for explicit plan import, durable `.dispatch/` state, status, tail, and future mechanical orchestration.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Boundary docs and skill flow | validated | codex-worker-a | main |  | 2026-05-02 |
| 02 | Plan schema and `init --plan` | validated | Worker B | main |  | 2026-05-02 |
| 03 | Remove runtime inspect/heuristic plan | validated | Worker C | main | 02 | 2026-05-02 |
| 04 | Orchestrator loop design | validated | codex-worker-a | main | 01 | 2026-05-02 |
| 05 | Validation and handoff | validated | codex | main | 01, 02, 03, 04 | 2026-05-02 |

## Activity Log

- 2026-05-02 codex: created corrective spec after product review found that runtime-owned repository inspection and heuristic planning were the wrong layer.
- 2026-05-02 codex: recorded `.dispatch/` as the only storage location for Dispatch Engine-generated non-project runtime content.
- 2026-05-02 codex-worker-a: validated workstreams 01 and 04; docs now state the explicit-plan boundary and future imported-plan orchestrator loop.
- 2026-05-02 Worker B: claimed workstream 02 for explicit plan schema validation and `init --plan` runtime import.
- 2026-05-02 Worker B: validated workstream 02 with unit tests, CLI help/version checks, explicit plan init/status/tail smoke checks, and `git diff --check`.
- 2026-05-02 Worker C: claimed workstream 03 to remove runtime-owned inspect and heuristic plan behavior.
- 2026-05-02 Worker C: validated workstream 03 with full unit tests, CLI help/version checks, explicit plan import/status/tail smoke checks, old-command nonzero checks, and `git diff --check`.
- 2026-05-02 codex: reviewed worker outputs, fixed small integration documentation/event payload mismatches, and validated the full corrective change with unit tests, CLI help/version, removed-command checks, explicit plan import/status/tail smoke in a temporary repo, grep review, and `git diff --check`.
