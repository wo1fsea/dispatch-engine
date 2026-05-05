---
spec_id: gh-5-windows-launch-cancel
language: en-US
audience: agent
doc_type: spec
status: planned
created: 2026-05-04
updated: 2026-05-04
issue: https://github.com/wo1fsea/dispatch-engine/issues/5
---

# Windows Launch And Cancel Tech Spec

## Current Evidence

Fresh Windows validation on 2026-05-04 produced these failures:

- `PYTHONPATH=scripts python -m unittest discover -s tests`: 90 tests run, 5
  failures and 3 errors.
- Live and detached coordinator tests failed because extensionless fake provider
  scripts were not launchable by Windows process creation.
- Copied skill E2E failed when the fake `codex` provider could not be executed.
- `test_coordinator_prompt_template_is_centralized_under_references` failed
  because it searched for `references/prompts` in a Windows path string.
- Earlier dogfood in issue #5 showed `de run --dry-run` resolving
  `codex.CMD`, while live launch still invoked `codex` and failed.
- Earlier dogfood in issue #5 showed `DefaultProcessController.is_alive()`
  crashing on Windows process liveness checks instead of treating stale process
  state as not running.

## Change Gate

- Problem: Windows hosts cannot reliably launch resolved provider executables
  or cancel stale process state, and tests use POSIX-only fake executable
  shapes.
- Existing path considered: Keep using rendered provider argv directly for live
  launch and keep extensionless fake provider scripts.
- Why existing path is insufficient: The dry-run preflight can find the real
  Windows executable, but live launch ignores that resolved path; Windows also
  cannot execute extensionless shebang scripts like POSIX.
- Smallest new surface: Internal helper(s) for executable launch argv and
  cross-platform fake provider test creation.
- What will be deleted or replaced: No public CLI surface is replaced.
- Owner: Dispatch Engine maintainers.
- Validation: Focused Windows regression tests, full unittest discovery, CLI
  smoke checks, and `git diff --check`.
- Temporary or permanent: Permanent portability behavior.
- Removal condition: None.

## Implementation Surface

Expected files:

- `scripts/dispatch_engine/coordinators.py`
- `scripts/dispatch_engine/cancel.py`
- `tests/test_live_coordinator_supervision.py`
- `tests/test_detached_coordinator_supervision.py`
- `tests/test_skill_install_e2e.py`
- `tests/test_run_dry_run.py`
- `tests/test_run_cancel_control.py`
- `specs/gh-5-windows-launch-cancel/STATUS.md`
- `specs/gh-5-windows-launch-cancel/workstreams/*.md`

Docs beyond the spec are only required if behavior visible in README/SKILL
changes. The intended runtime behavior matches existing docs; this spec should
record the Windows-specific validation evidence.

## Launch Design

`_render_argv()` remains the source of the provider command shape. Dry-run and
live payloads continue to expose that rendered command in `argv`.

Live process execution should use a small internal helper:

```python
def _execution_argv(argv: list[str], executable_path: str) -> list[str]:
    return [executable_path, *argv[1:]]
```

This keeps the public/audit command stable while making `subprocess.run()` use
the executable discovered by `shutil.which()`. The helper should be tested with
a Windows-style resolved executable such as `C:\\Users\\x\\AppData\\Roaming\\npm\\codex.CMD`.

## Test Provider Design

Tests that create fake provider executables should write a Windows-launchable
command file on Windows:

```text
codex.cmd -> python fake_provider.py
claude.cmd -> python fake_provider.py
```

On POSIX, the existing executable shebang script remains sufficient. The fake
provider helpers should preserve the observed provider argv so existing tests
still assert that the provider receives the same command arguments after
`argv[0]`.

## Cancel Design

`DefaultProcessController.is_alive()` should treat stale Windows process state
as not running. At minimum, catch the observed `SystemError` from `os.kill(pid,
0)` and return `False`.

`_signal_process()` currently catches `OSError` around `process_controller`
calls. If a Windows controller raises `SystemError` from liveness checks, the
default controller should absorb it before `_signal_process()` sees it. Tests
should prove cancellation completes and records `final_state: "not_running"`
when `is_alive()` returns false for stale process state.

## Workstreams

1. `01-launch-runtime-tests`: provider launch helper plus foreground/detached
   and copied-skill fake provider portability.
2. `02-cancel-windows-liveness`: stale Windows PID handling and focused cancel
   regression tests.
3. `03-status-docs-validation`: path normalization, spec status updates, full
   validation, and final review evidence.

## Validation

Focused:

```bash
$env:PYTHONPATH='scripts'; python -m unittest tests.test_live_coordinator_supervision -v
$env:PYTHONPATH='scripts'; python -m unittest tests.test_detached_coordinator_supervision -v
$env:PYTHONPATH='scripts'; python -m unittest tests.test_skill_install_e2e -v
$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_cancel_control -v
$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_dry_run -v
```

Full:

```bash
$env:PYTHONPATH='scripts'; python -m unittest discover -s tests
python scripts/de.py --help
python scripts/de.py version
python scripts/de.py run --help
python scripts/de.py cancel --help
python scripts/de.py stop --help
git diff --check
```

## Risks

- A test-only fake provider helper could accidentally assert fake-provider
  behavior rather than runtime behavior. Keep assertions focused on the real
  provider argv and durable state.
- Replacing `argv[0]` at execution time must not change the JSON contract or
  dry-run output.
- Windows process signalling semantics differ from POSIX; cancellation should
  prefer durable terminal state and clear signal outcome reporting over
  pretending all signals are portable.

