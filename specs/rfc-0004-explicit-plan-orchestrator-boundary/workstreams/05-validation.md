---
workstream_id: 05-validation
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex
branch: main
updated: 2026-05-02
depends_on:
  - 01-boundary-docs
  - 02-plan-schema-init
  - 03-remove-inspect-plan
  - 04-orchestrator-loop-design
---

# Validation And Handoff

## Scope

Validate the corrected architecture and prepare the spec for review.

## Files

- `specs/rfc-0004-explicit-plan-orchestrator-boundary/STATUS.md`
- `specs/README.md`
- any docs touched by earlier workstreams

## Requirements

- Run the full test suite.
- Run CLI smoke checks for help, version, init, status, and tail.
- Confirm `.dispatch/` is ignored and contains generated runtime files.
- Confirm old runtime-owned inspect/plan guidance is gone or migration-only.
- Update `STATUS.md` rows and activity log with evidence.

## Validation

```bash
python3 scripts/de.py --help
python3 scripts/de.py version
PYTHONPATH=scripts python3 -m unittest discover -s tests
git status --short
```

## Activity Log

- 2026-05-02 codex: validated the integrated corrective change. Evidence: `PYTHONPATH=scripts python3 -m unittest discover -s tests`; `python3 scripts/de.py --help`; `python3 scripts/de.py version`; `python3 scripts/de.py inspect .` exits 2; `python3 scripts/de.py plan . --objective smoke` exits 2; explicit plan `init`, `status`, and `tail` smoke in a temporary target repository; `rg "inspect|plan --objective" SKILL.md README.md references specs/rfc-0003-runtime-state-and-tail/STATUS.md specs/rfc-0004-explicit-plan-orchestrator-boundary`; `find . -path './.dispatch/*' -maxdepth 4 -type f`; `git diff --check`.
