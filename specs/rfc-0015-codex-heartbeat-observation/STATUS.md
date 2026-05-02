---
spec_id: rfc-0015-codex-heartbeat-observation
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: partial
validation: passed-baseline
coordinator: dispatch-engine
updated: 2026-05-02
---

# Status

## Summary

Ready. This spec records the corrected observation architecture: detached
Dispatch Engine runs remain visible through durable `.dispatch/` state, while
foreground Codex can only explain background progress after a user message or a
host-provided thread heartbeat wakes it.

The spec and guidance baseline is complete. Runtime control-surface work remains
planned for follow-up implementation.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Spec and guidance baseline | validated | codex | main | rfc-0014 | 2026-05-02 |
| 02 | Codex-facing control surface | planned | codex | main | 01 | 2026-05-02 |
| 03 | Host heartbeat runbook | planned | codex | main | 01 | 2026-05-02 |
| 04 | Validation and dogfood | planned | codex | main | 02, 03 | 2026-05-02 |

## Validation

- `python3 scripts/de.py --help`
- `python3 scripts/de.py status --help`
- `git diff --check`
