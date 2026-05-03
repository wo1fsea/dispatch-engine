---
spec_id: gh-5-windows-launch-cancel
workstream_id: 03-status-docs-validation
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: interactive-codex
branch: codex/windows-adaptation-spec
created: 2026-05-04
updated: 2026-05-04
depends_on:
  - 01-launch-runtime-tests
  - 02-cancel-windows-liveness
files:
  - tests/test_run_dry_run.py
  - specs/gh-5-windows-launch-cancel/STATUS.md
---

# Status Docs Validation

## Scope

Remove Windows-only false failures from path assertions, run final validation,
and update this spec's status evidence.

## Requirements

- Fix prompt-template tests to assert path parts or normalized paths instead of
  hard-coded `references/prompts`.
- Run focused tests from workstreams 01 and 02.
- Run full unittest discovery and CLI smoke checks.
- Update `STATUS.md` summary, workstream rows, and validation evidence.
- Keep issue #4 out of scope unless the user explicitly expands this spec.

## Acceptance

1. `tests.test_run_dry_run` passes on Windows.
2. Full unittest discovery passes with `PYTHONPATH=scripts`.
3. CLI smoke checks pass.
4. `STATUS.md` records validation commands and results.

## Validation

```powershell
$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_dry_run -v
$env:PYTHONPATH='scripts'; python -m unittest discover -s tests
python scripts/de.py --help
python scripts/de.py version
python scripts/de.py run --help
python scripts/de.py cancel --help
python scripts/de.py stop --help
git diff --check
```

## Activity Log

- 2026-05-04: Validated by interactive Codex after workstreams 01 and 02
  returned. Full unittest discovery passed with 91 tests; CLI smoke checks and
  `git diff --check` passed.
