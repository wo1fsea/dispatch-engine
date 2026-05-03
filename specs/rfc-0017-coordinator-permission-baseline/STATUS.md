---
language: en-US
audience: mixed
doc_type: status
status: ready
created: 2026-05-03
updated: 2026-05-03
---

# Status

## Summary

Ready for review. The baseline is implemented directly in provider coordinator
profiles: Codex coordinators launch with `--sandbox danger-full-access`, Claude
coordinators launch with bypass permissions, and worker permissions remain
assigned by the coordinator through durable Dispatch Engine scope records.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01-runtime-launch-args | Provider profile argv and tests | ready | Codex | local | none | 2026-05-03 |
| 02-docs-and-prompts | Skill, references, prompt templates, and validation | ready | Codex | local | 01-runtime-launch-args | 2026-05-03 |

## Validation Log

- `PYTHONPATH=scripts python3 -m unittest tests.test_run_dry_run` passed.
- `PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision` passed.
- `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed: 66 tests.
- `python3 scripts/de.py run --help` passed.
- `git diff --check` passed.
