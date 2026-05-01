---
workstream_id: 01-boundary-docs
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex-worker-a
branch: main
updated: 2026-05-02
depends_on: []
---

# Boundary Docs And Skill Flow

## Scope

Update the skill and operator-facing docs so Dispatch Engine is described as an explicit-plan runtime operated by interactive Codex.

## Files

- `SKILL.md`
- `README.md`
- `references/operator-flow.md`
- `references/event-protocol.md`
- `references/worker-protocol.md`
- `specs/rfc-0003-runtime-state-and-tail/STATUS.md`

## Requirements

- Remove instructions that tell operators to use runtime `inspect` for repository discovery.
- Remove instructions that tell operators to use runtime `plan --objective` for workstream splitting.
- State that Codex reads repo instructions and creates an explicit dispatch plan.
- State that Dispatch Engine writes non-project runtime content only under `.dispatch/`.
- Add a supersession note for the `rfc-0003` inspect/plan workstream.

## Validation

```bash
rg "inspect|plan --objective" SKILL.md README.md references specs/rfc-0003-runtime-state-and-tail/STATUS.md
```

Any remaining matches must be historical, migration-only, or explicitly marked as superseded.

## Activity Log

- 2026-05-02 codex-worker-a: claimed workstream on main.
- 2026-05-02 codex-worker-a: updated skill, README, operator flow, event protocol, worker protocol, and rfc-0003 supersession notes for the explicit-plan boundary.
- 2026-05-02 codex-worker-a: validated grep output; remaining matches are historical, migration-only, or supersession-only.
