---
workstream_id: 04-orchestrator-loop-design
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex-worker-a
branch: main
updated: 2026-05-02
depends_on:
  - 01-boundary-docs
---

# Orchestrator Loop Design

## Scope

Document the future execution loop without implementing real worker launch yet.

## Files

- `references/operator-flow.md`
- `references/worker-protocol.md`
- optional new reference: `references/orchestrator-loop.md`

## Requirements

- Describe the main runtime orchestrator as consuming imported plan state.
- Describe serial and parallel scheduling based on `depends_on`, `parallel_group`, and write-scope safety.
- Describe worker prompt generation from workstream state.
- Describe reviewer acceptance as a separate phase before workstream completion.
- Describe how interactive Codex can keep talking to the user while polling `status` and `tail`.
- Keep this design adapter-neutral; do not require one specific agent provider.

## Validation

Docs review checklist:

- The loop starts from imported plan state, not repo inspection.
- User interaction stays in external Codex.
- Runtime state and generated reports stay under `.dispatch/`.
- Reviewer gates are explicit before completion.

## Activity Log

- 2026-05-02 codex-worker-a: claimed workstream on main after boundary docs.
- 2026-05-02 codex-worker-a: added `references/orchestrator-loop.md` and linked the future imported-plan scheduler, worker, reviewer, validation, status, and tail loop from operator and worker references.
- 2026-05-02 codex-worker-a: validated design checklist in docs review.
