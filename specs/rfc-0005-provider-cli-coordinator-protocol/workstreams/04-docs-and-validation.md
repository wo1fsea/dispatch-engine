---
workstream_id: 04-docs-and-validation
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker D
branch: ""
updated: 2026-05-02
depends_on:
  - 01-agent-state-protocol
  - 02-status-observability
  - 03-run-launcher-dry-run
---

# Docs And Validation

## Scope

Update operator and protocol documentation, validate the integrated change, and prepare the spec for review.

## Files

- `SKILL.md`
- `README.md`
- `references/orchestrator-loop.md`
- `references/event-protocol.md`
- `references/worker-protocol.md`
- `specs/rfc-0005-provider-cli-coordinator-protocol/STATUS.md`
- `specs/README.md`

## Requirements

- Document provider CLI coordinator launch after explicit plan import.
- Document that omitted `--provider` defaults to Codex.
- Document explicit `--provider codex` and `--provider claude` dry-run behavior.
- State that Codex uses a `codex exec --sandbox danger-full-access` command shape and Claude uses a `claude --dangerously-skip-permissions --permission-mode bypassPermissions -p` command shape, with exact prompt/input/context arguments finalized by implementation.
- State that coordinators are coordinator-only and must not implement project-file changes directly.
- State that workers, reviewers, and validators must be registered in Dispatch Engine state.
- Document `.dispatch/runs/<run-id>/agents/`, reports, logs, and heartbeats.
- Document required lifecycle and protocol violation events.
- Update status rows and activity log with implementation evidence.
- Verify all new durable docs include metadata.

## Validation

```bash
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py status .
python3 scripts/de.py tail .
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg -n "provider codex|provider claude|codex exec|claude|coordinator-only|agent.spawned|protocol.violation|heartbeats|agents/" SKILL.md README.md references specs/rfc-0005-provider-cli-coordinator-protocol
git diff --check
```

## Activity Log

- 2026-05-02 Worker D: validated with `python3 scripts/de.py --help`, `python3 scripts/de.py version`, temp explicit plan import, default Codex dry-run, explicit Codex dry-run, explicit Claude dry-run, `status`, `status --json`, `tail`, full unittest discovery, required `rg` documentation check, and `git diff --check`.
- 2026-05-02 Worker D: claimed workstream and updated operator/reference docs for `de run --dry-run`, default Codex provider behavior, explicit Codex and Claude provider rendering, coordinator-only boundaries, registered implementation agents, agent state directories, lifecycle events, status counts, heartbeats, and protocol violations.
- 2026-05-02 Worker S: initialized workstream as ready.
