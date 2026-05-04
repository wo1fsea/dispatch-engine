---
language: en-US
audience: mixed
doc_type: spec
---

# Provider-Native Worker Lifecycle Product Spec

## Summary

Dispatch Engine should make provider-native spawned workers observable even when
the provider accepts a spawn but the worker never initializes or never writes a
report.

This spec covers GitHub issues #15 and #18. The common product problem is that
Dispatch Engine currently has a narrow launch-evidence model and no durable
status diagnostic for provider-native workers that remain active without
required output.

## Goals / Non-goals

- Goal: Recognize provider-native spawn evidence consistently across canonical
  and nested fields already produced by dogfood coordinators.
- Goal: Avoid false `missing_agent_launch_evidence` alerts when a worker has
  valid provider-native spawn evidence.
- Goal: Surface a material diagnostic when a provider-native worker is active
  but has no required report after observable heartbeat/spawn evidence.
- Goal: Make the diagnostic actionable for interactive Codex: inspect, wait,
  mark blocked/failed, repair, or cancel.
- Goal: Update coordinator/operator guidance so future workers write canonical
  launch evidence fields.
- Non-goal: Implement a provider API poller for Codex `spawn_agent` status.
- Non-goal: Implement a DE-owned worker scheduler or launcher.
- Non-goal: Automatically kill provider-native worker sessions.

## Behavior Invariants

1. `de status --json` treats any of these as launch evidence for an active
   worker/reviewer/validator:
   - `provider_native_agent_id`
   - `provider_native_spawn_ref`
   - `launch_evidence.spawn_agent_id`
   - `launch_evidence.provider_native_spawn_ref`
   - `provider_launch.evidence.provider_native_spawn_ref`
   - positive `pid`
   - existing stdout/stderr log file
2. Launch evidence diagnostics should name the exact accepted evidence fields
   or missing fields.
3. An active provider-native implementation agent with launch evidence but no
   role-specific report is surfaced as a lifecycle diagnostic when it is stale
   enough to require operator attention.
4. The stale/no-report diagnostic appears in both `status --json`
   `lifecycle_diagnostics` and `alerts --json`.
5. Terminal cancelled runs do not produce noisy next actions, but their alerts
   and lifecycle diagnostics may still document material historical evidence
   when useful.
6. Coordinator guidance says to write `provider_native_agent_id` as the
   canonical field, while runtime remains compatible with dogfood nested
   evidence fields.

## States And Edge Cases

- Spawned and running with canonical provider id: no missing-launch diagnostic.
- Spawned and running with only nested provider launch evidence: no
  missing-launch diagnostic.
- Spawned and running with no report and stale heartbeat: material no-report
  diagnostic.
- Spawned and cancelled with no report: no active next action; status may
  retain cancellation reason and evidence.
- Running with only placeholder stdout/stderr paths that do not exist: still
  missing launch evidence.
- Running with a valid report path and report file: no no-report diagnostic.

## Open Questions

- What default staleness interval should be used before surfacing the
  no-report diagnostic?
- Should provider-native pending-init be a distinct agent status in a future
  spec?
