---
id: 04-docs-validation
language: en-US
audience: agent
doc_type: spec
status: validated
owner: codex-worker
branch: main
pr:
files:
  - references/event-protocol.md
  - README.md
  - specs/rfc-0003-runtime-state-and-tail/**
depends_on:
  - 01-runtime-state
  - 02-status-tail
  - 03-inspect-plan
claimed_at: 2026-05-02T00:00:00+08:00
lease_expires_at:
updated: 2026-05-02
---

# Documentation And Validation Workstream

## Scope

Document the expanded event protocol and record validation evidence for the runtime-state and tail work.

## Plan

1. Update `references/event-protocol.md`.
2. Update README examples only if CLI usage changes materially.
3. Record validation evidence in this workstream and `STATUS.md`.
4. Confirm no `.dispatch/` state is staged.

## Progress

- Claimed by codex-worker on main.
- Documented expanded runtime state, event types, CLI readers, and append-only decision log behavior in `references/event-protocol.md`.
- Updated README smoke examples to use `python3` and include inspect/plan/status/tail commands.
- Validated required CLI commands, unittest discovery, manual missing-run behavior, generated state shape, and git ignore/staging behavior.

## Validation

- 2026-05-02: `python3 scripts/de.py --help` passed.
- 2026-05-02: `python3 scripts/de.py version` passed and printed `0.1.0`.
- 2026-05-02: `python3 scripts/de.py inspect .` passed.
- 2026-05-02: `python3 scripts/de.py inspect . --json` passed.
- 2026-05-02: `python3 scripts/de.py plan . --objective "smoke test objective"` passed and generated `.dispatch/runs/20260501T181514429586Z`.
- 2026-05-02: `python3 scripts/de.py status .` passed.
- 2026-05-02: `python3 scripts/de.py tail .` passed and printed `run.created` and `workstream.planned`.
- 2026-05-02: `python3 scripts/de.py status . --json` passed.
- 2026-05-02: `python3 scripts/de.py tail . --json` passed.
- 2026-05-02: `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed, 8 tests.
- 2026-05-02: generated run state contained `run.json`, `events.jsonl`, `decisions.jsonl`, `workstreams/01-implementation.json`, and `artifacts/`.
- 2026-05-02: missing-run manual checks passed with `No Dispatch Engine runs found.` for `status` and `tail` in a temporary empty directory.
- 2026-05-02: explicit missing run id manual checks passed with `Run not found: missing` for `status` and `tail`.
- 2026-05-02: `git check-ignore -v .dispatch .dispatch/runs .dispatch/runs/*` confirmed `.dispatch/` is ignored by `.gitignore`.
- 2026-05-02: `git diff --cached --name-only -- .dispatch` returned no staged files.
- 2026-05-02: cleaned generated `.dispatch/` and `__pycache__/`; final `git status --short` shows only scoped documentation/status files.

## Documentation Evidence

- Docs updated / N/A: `references/event-protocol.md`; README examples updated for `python3` and current smoke commands.
- Language/audience/doc type declared: existing metadata preserved in touched docs.
- Source of truth: `references/event-protocol.md` is the event and run-state protocol reference.
- Routers or indexes updated: N/A; no new docs or paths.
- Links checked: N/A; no new links.
- Examples or commands checked: required `python3` CLI command list passed.
- Generated docs regenerated / N/A: N/A.
- Stale docs removed or superseded: `plan.created` documented as historical and superseded by `run.created`.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
- 2026-05-02 codex-worker: claimed `04-docs-validation` on main.
- 2026-05-02 codex-worker: validated `04-docs-validation`; documentation evidence, full Python 3 CLI smokes, unittest discovery, manual edge checks, and generated state cleanup complete.
