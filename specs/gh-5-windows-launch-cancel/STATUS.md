---
spec_id: gh-5-windows-launch-cancel
language: en-US
audience: agent
doc_type: status
status: ready-review
implementation: complete
validation: passed
coordinator: interactive-codex
created: 2026-05-04
updated: 2026-05-04
issue: https://github.com/wo1fsea/dispatch-engine/issues/5
---

# Status

## Summary

Ready for review. This spec fixes Windows provider launch and cancel process
handling exposed by issue #5 and by local Windows test runs. GitHub issues #4,
#6, and #7 remain open and out of scope for this spec.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01-launch-runtime-tests | Resolved executable launch and Windows-launchable fake providers | validated | worker-launch | codex/windows-adaptation-spec | none | 2026-05-04 |
| 02-cancel-windows-liveness | Windows stale PID liveness handling and cancel regression tests | validated | worker-cancel | codex/windows-adaptation-spec | none | 2026-05-04 |
| 03-status-docs-validation | Path normalization, spec status, and full validation evidence | validated | interactive-codex | codex/windows-adaptation-spec | 01-launch-runtime-tests, 02-cancel-windows-liveness | 2026-05-04 |

## Acceptance Criteria

1. Foreground live coordinator tests pass on Windows.
2. Detached coordinator tests pass on Windows.
3. Copied skill install E2E passes on Windows.
4. Cancel control tests cover and pass stale Windows PID handling.
5. Prompt-template path assertions pass on Windows and POSIX.
6. Full unittest discovery passes with `PYTHONPATH=scripts`.
7. CLI smoke checks for help/version/run/cancel/stop pass.
8. Spec status records validation evidence and issues #4, #6, and #7 remain
   out of scope.

## Validation Plan

- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_live_coordinator_supervision -v`
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_detached_coordinator_supervision -v`
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_skill_install_e2e -v`
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_cancel_control -v`
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_dry_run -v`
- `$env:PYTHONPATH='scripts'; python -m unittest discover -s tests`
- `python scripts/de.py --help`
- `python scripts/de.py version`
- `python scripts/de.py run --help`
- `python scripts/de.py cancel --help`
- `python scripts/de.py stop --help`
- `git diff --check`

## Validation Evidence

- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_live_coordinator_supervision -v`: passed, 4 tests.
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_detached_coordinator_supervision -v`: passed, 2 tests.
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_skill_install_e2e -v`: passed, 1 test.
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_cancel_control -v`: passed, 6 tests.
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_dry_run -v`: passed, 6 tests.
- `$env:PYTHONPATH='scripts'; python -m unittest tests.test_dogfood_runbook_fixture -v`: passed, 1 test.
- `$env:PYTHONPATH='scripts'; python -m unittest discover -s tests`: passed, 91 tests.
- `python scripts/de.py --help`: passed.
- `python scripts/de.py version`: passed, `0.1.0`.
- `python scripts/de.py run --help`: passed.
- `python scripts/de.py cancel --help`: passed.
- `python scripts/de.py stop --help`: passed.
- `git diff --check`: passed with Git CRLF normalization warnings only.

## Activity Log

- 2026-05-04: Created ready spec from Windows test failures and GitHub issue
  #5. Open issue #4 was reviewed and left out of scope as a separate worker
  report schema contract problem.
- 2026-05-04: Coordinator claimed workstreams 01 and 02 for parallel
  implementation subagents; status/docs validation remains ready until both
  implementation workstreams return.
- 2026-05-04: worker-launch implemented resolved executable launch and
  Windows-launchable fake providers. Main-session review added remaining
  dogfood fixture fake-provider coverage.
- 2026-05-04: worker-cancel implemented stale Windows PID liveness handling and
  regression coverage.
- 2026-05-04: Main-session review fixed path-normalized prompt-template
  assertions, ran focused and full validation, and marked the spec
  ready-review. GitHub issues #4, #6, and #7 remain out of scope as separate
  report-schema/protocol work.
