---
spec_id: rfc-0005-provider-cli-coordinator-protocol
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
coordinator: dispatch-engine
updated: 2026-05-02
---

# Status

## Summary

Ready for review. Workstreams 01 through 04 are validated: Dispatch Engine now has durable agent registry helpers, status observability for registered agents and violations, dry-run provider coordinator rendering for default Codex, explicit Codex, and explicit Claude, and updated operator/reference documentation. Codex is the default provider when `--provider` is omitted, Codex renders `codex exec`, Claude renders `claude -p`, and dry-run renders command/prompt details without launching a provider process.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Agent state protocol | validated | Worker A | main |  | 2026-05-02 |
| 02 | Status observability | validated | Worker B | main | 01 | 2026-05-02 |
| 03 | Run launcher dry-run | validated | Worker C |  | 01 | 2026-05-02 |
| 04 | Docs and validation | validated | Worker D |  | 01, 02, 03 | 2026-05-02 |

## Activity Log

- 2026-05-02 Worker D: validated workstream 04 docs and validation with CLI help/version, temp explicit plan import, default Codex dry-run, explicit Codex dry-run, explicit Claude dry-run, status, status JSON, tail, full unittest discovery, required documentation grep, and `git diff --check`; marked rfc-0005 ready-review.
- 2026-05-02 Worker D: claimed workstream 04 docs and validation and updated docs/status surfaces for the integrated rfc-0005 implementation.
- 2026-05-02 Worker B: validated workstream 02 status observability with read-only agent counts by role/status, coordinator provider/profile/status fields, active assignments, heartbeat summary, protocol violation summaries, human status agent lines, focused and full unit tests, temp-run status smoke checks, and `git diff --check`.
- 2026-05-02 Worker C: validated workstream 03 run launcher dry-run with read-only provider rendering, focused/unit tests, CLI smokes, and `git diff --check`.
- 2026-05-02 Worker C: claimed workstream 03 run launcher dry-run.
- 2026-05-02 Worker A: validated workstream 01 agent state protocol with durable agent registry helpers, run supervision directories, lifecycle event helpers, protocol violation checks, focused tests, full unittest discovery, and `git diff --check`.
- 2026-05-02 Worker S: created ready RFC for provider CLI coordinator protocol with Codex default provider behavior, explicit Claude provider support, coordinator-only boundary, observable implementation agents, required state direction, event vocabulary, status expectations, and parallel implementation workstreams.

## Review Notes

- Current dry-run implementation includes helper writers for `coordinator.started`, `agent.spawned`, `agent.heartbeat`, `workstream.assigned`, `agent.completed`, `agent.failed`, `protocol.violation`, and `decision.requested`. `coordinator.completed` and `coordinator.failed` remain live-supervision vocabulary and are not emitted by the dry-run renderer.
- Runtime prompt templates are centralized under `references/prompts/`. The current coordinator protocol prompt lives in `references/prompts/coordinator-protocol.md` and is rendered through `scripts/dispatch_engine/prompts.py`.

## Spec Handoff

- Spec path: `specs/rfc-0005-provider-cli-coordinator-protocol`
- Status: ready-review
- Spec type: architecture/runtime protocol
- Open questions: none blocking
- Workstreams: `01-agent-state-protocol`, `02-status-observability`, `03-run-launcher-dry-run`, `04-docs-and-validation`
- Next owner: implementation coordinator
- Validation expectation: unit tests, CLI dry-run smoke checks for default Codex, explicit Codex, and explicit Claude, docs metadata checks, `git diff --check`
- Ready to implement: implemented and ready for review
