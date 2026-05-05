---
language: en-US
audience: agent
doc_type: router
---

# Specs

Use `docs/governance/spec-production.md` for creating specs, `docs/governance/spec-workflow.md` for the spec lifecycle, `docs/governance/spec-id-policy.md` for id format, `docs/governance/spec-execution-status.md` for execution status, and `docs/governance/multi-agent-spec-flow.md` for parallel implementation.

Each substantial spec should live under:

```text
specs/<source>-<id>-<short-slug>/
  PRODUCT.md
  TECH.md
  STATUS.md
  workstreams/
    01-implementation.md
```

## Current Specs

- `rfc-0001-initial-governance`: initial repository governance.
- `rfc-0002-skill-first-packaging`: root-level runtime-backed skill packaging.
- `rfc-0003-runtime-state-and-tail`: self-dogfood spec for durable run state, status, tail, inspect, and plan improvements.
- `rfc-0004-explicit-plan-orchestrator-boundary`: corrective spec that replaces runtime-owned inspect/heuristic plan with Codex-owned discovery, explicit dispatch plans, and `.dispatch/` runtime storage.
- `rfc-0005-provider-cli-coordinator-protocol`: provider CLI coordinator launch protocol with Codex as the default provider, explicit Claude provider support, coordinator-only boundaries, observable registered subagents, agent state, events, heartbeats, and status reporting.
- `rfc-0006-live-coordinator-supervision`: validated foreground provider CLI coordinator process supervision with prompt snapshots, stdout/stderr logs, and coordinator completion/failure events.
- `rfc-0007-worker-adapter-protocol`: active helper-first worker adapter protocol for registered implementation agents, centralized worker prompt snapshots, durable worker reports, status visibility, and conservative protocol violations.
- `rfc-0008-coordinator-spawn-contract`: validated coordinator-spawn contract clarifying that the provider coordinator owns subagent spawn decisions while Dispatch Engine owns durable registration, prompt snapshot, heartbeat, report, event, status, and violation state.
- `rfc-0009-review-validator-report-protocol`: ready skill-first reviewer/validator evidence protocol with minimal durable report validation.
- `rfc-0010-workstream-acceptance-guidance`: ready skill-first workstream state and acceptance guidance with minimal evidence checks.
- `rfc-0011-decision-blocker-protocol`: ready decision/blocker protocol for durable operator questions and pending-decision visibility.
- `rfc-0012-dogfood-runbook-fixture`: ready repeatable fake-provider dogfood runbook and fixture path.
- `rfc-0013-skill-install-operator-docs`: validated install, quickstart, and troubleshooting documentation path for the first usable version.
- `rfc-0014-detached-coordinator-supervisor`: validated detached coordinator supervisor so interactive Codex can start `de run --detach` and continue polling status/tail.
- `rfc-0015-codex-heartbeat-observation`: validated Codex-facing observation contract for detached runs, host heartbeat wakeups, JSON-first control surfaces, and decision/status interpretation.
- `rfc-0016-autonomous-decision-records`: validated structured `.dispatch/` record format for autonomous technical decisions made by outer Codex after four unanswered heartbeat checks.
- `rfc-0017-coordinator-permission-baseline`: validated high-permission coordinator launch baseline for Codex and Claude, with worker permission scope delegated to the coordinator.
- `rfc-0018-agent-capability-profiles`: validated explicit capability profile contract for workstreams and agents, covering non-file permissions, escalation decisions, and status/report auditing.
- `rfc-0019-validator-report-schema-diagnostics`: validated validator report schema diagnostics and regression fixture for useful dogfood evidence reported as malformed.
- `rfc-0021-provider-native-worker-lifecycle`: ready provider-native launch evidence and no-report lifecycle diagnostics for dogfood issues #15 and #18.
- `rfc-0022-protocol-violation-status-accuracy`: ready diagnostic accuracy fixes for current dogfood issue #16 scope.
- `rfc-0020-run-cancel-control`: validated Codex-facing cancellation control for detached runs, including `de cancel`, `de stop`, durable cancelled state, events, alerts, and heartbeat shutdown guidance.
- `rfc-0023-protocol-violation-resolution`: validated durable protocol-violation acknowledgement/supersession records for dogfood issue #19.
- `rfc-0024-dashboard-autostart-observer`: locally committed dashboard observer and prototype-parity baseline, including `de dashboard`, read-only browser surfaces, theme/density preferences, event-tail resize, explicit empty states, and captured prototype assets.
- `rfc-0025-safe-parallel-dispatch-contract`: ready safe parallel dispatch contract for issue #22, requiring explicit parallelism analysis, ready-set coordinator dispatch, serial rationale, and optional warning-only plan diagnostics.
