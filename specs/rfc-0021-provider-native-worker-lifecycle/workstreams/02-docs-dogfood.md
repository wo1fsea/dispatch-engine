---
workstream_id: 02-docs-dogfood
status: merged
owner: Worker A
branch: local
claimed_at: 2026-05-04
updated: 2026-05-04
---

# Docs And Dogfood Evidence

## Scope

Update coordinator/operator/heartbeat guidance and record dogfood validation
for #15/#18 evidence.

## Files

- `references/prompts/coordinator-protocol.md`
- `references/operator-guide.md`
- `references/heartbeat-observation.md`
- `references/event-protocol.md` when status/alert semantics change
- `specs/rfc-0021-provider-native-worker-lifecycle/STATUS.md`

## Acceptance

- Docs name `provider_native_agent_id` as canonical.
- Docs mention compatibility launch evidence fields recognized by status.
- Docs explain active provider-native no-report diagnostics and recovery.
- Dogfood command evidence is recorded in `STATUS.md`.

## Activity Log

- 2026-05-04 codex: workstream created.
- 2026-05-04 Worker A: claimed prompt/operator/heartbeat/event reference updates for rfc-0021.
- 2026-05-04 Worker A: updated coordinator, operator, heartbeat, and event protocol references for canonical provider-native launch evidence, compatibility fields, and `provider_native_spawn_without_report`; dogfood status checks returned `status: ok`.
- 2026-05-04 codex: reviewed docs and dogfood evidence and accepted into main.
