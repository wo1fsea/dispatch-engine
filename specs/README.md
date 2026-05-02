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
