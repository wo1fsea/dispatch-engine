---
spec_id: rfc-0014-detached-coordinator-supervisor
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

Validated. Dispatch Engine now supports detached coordinator supervision through
`de run --detach`, allowing interactive Codex to keep talking with the user
while a background supervisor runs the provider coordinator and writes durable
`.dispatch/` state.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Detached supervisor runtime | validated | codex | main | rfc-0013 | 2026-05-02 |
| 02 | Status/docs validation | validated | codex | main | 01 | 2026-05-02 |

## Validation

- `PYTHONPATH=scripts python3 -W error::ResourceWarning -m unittest tests.test_detached_coordinator_supervision`
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- `python3 scripts/de.py run --help`
- `git diff --check`
