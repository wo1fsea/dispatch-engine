---
spec_id: rfc-0021-provider-native-worker-lifecycle
language: en-US
audience: agent
doc_type: spec
status: done
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/15, https://github.com/wo1fsea/dispatch-engine/issues/18
updated: 2026-05-04
---

# Status

## Summary

Done. Runtime lifecycle implementation, reference updates, validation, and
main-session review are complete. This spec merges #15 and the launch-evidence
half of #18 into one provider-native lifecycle diagnostic update.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Runtime lifecycle diagnostics and tests | merged | Worker A | main |  | 2026-05-04 |
| 02 | Prompt/operator docs and dogfood evidence | merged | Worker A | main | 01 | 2026-05-04 |

## Activity Log

- 2026-05-04 codex: created spec from issue triage for #15 and #18.
- 2026-05-04 Worker A: claimed workstream 01 runtime lifecycle implementation.
- 2026-05-04 Worker A: claimed workstream 02 rfc-0021 reference updates.
- 2026-05-04 Worker A: validated rfc-0021 runtime lifecycle behavior and docs with focused tests, full unittest discovery, CLI help smoke checks, diff whitespace check, and dogfood status checks.
- 2026-05-04 codex: reviewed Worker A output, reran focused/full tests, CLI smoke, diff check, and dogfood status checks; accepted the implementation.

## Validation Evidence

- Red: `PYTHONPATH=scripts python3 -m unittest tests.test_status_tail` failed before implementation on missing accepted evidence fields, ignored nested provider-native evidence, and missing `provider_native_spawn_without_report`.
- Green: focused rfc-0021 lifecycle tests passed with `Ran 5 tests ... OK`.
- Broader validation: `PYTHONPATH=scripts python3 -m unittest tests.test_status_tail` passed with `Ran 15 tests ... OK`; `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed with `Ran 108 tests ... OK`.
- CLI smoke: `python3 scripts/de.py status --help` and `python3 scripts/de.py alerts --help` both exited 0.
- Diff check: `git diff --check` exited 0.
- Dogfood status: Agent Blackboard run `20260503T180517926231Z` and Paseo Passport run `20260503T183631153640Z` both returned `status: ok` with no lifecycle diagnostics.

## Spec Handoff

- Spec path: `specs/rfc-0021-provider-native-worker-lifecycle`
- Status: done
- Spec type: compact runtime/protocol bugfix
- Open questions: default stale/no-report threshold
- Workstreams: `01-runtime-lifecycle`, `02-docs-dogfood`
- Next owner: none
- Validation expectation: focused lifecycle tests, full unittest discovery,
  CLI smoke, dogfood status checks
- Ready to implement: complete
