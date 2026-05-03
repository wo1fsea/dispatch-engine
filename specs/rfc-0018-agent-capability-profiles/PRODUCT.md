---
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: mixed
doc_type: spec
status: planned
created: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/1
---

# Agent Capability Profiles Product Spec

## Problem

Alpha Kitchen dogfood showed that file and path scope are necessary but not
sufficient for Dispatch Engine agent governance. A worker can stay inside its
assigned files and still take surprising actions: fetch from the network,
install packages, start services, touch Docker, write runtime state, create
GitHub issues, or run expensive validation. Today those capabilities are
implicit in provider prompts and provider-specific permission flags, so the
operator cannot quickly audit what each agent was allowed to do.

RFC-0017 defines the high-permission coordinator launch baseline. This spec
defines the broader Dispatch Engine contract for workstream and agent
capability profiles. Provider enforcement remains provider-specific for now,
but the Dispatch Engine plan, prompt, report, status, decision, and validation
surfaces must make requested and granted capabilities explicit.

## Goals

- Define a durable capability profile contract for workstreams and spawned
  agents.
- Cover non-file capabilities such as network access, dependency resolution,
  Docker or service startup, test execution, repository write scope, runtime
  state writes, and GitHub issue creation.
- Make capability grants auditable in prompts, registration records, reports,
  status output, protocol violations, and final summaries.
- Define escalation rules when an agent needs a capability not granted by its
  profile.
- Keep the coordinator high-permission baseline from RFC-0017 intact while
  requiring the coordinator to grant narrower explicit profiles to workers,
  reviewers, and validators.
- Keep provider enforcement provider-specific; Dispatch Engine owns the
  explicit contract and evidence checks, not a universal sandbox.

## Non-Goals

- Build a provider-agnostic sandbox or operating system permission layer.
- Remove assigned files or allowed write roots from worker validation.
- Hard-code provider-native worker launch flags in the Dispatch Engine runtime.
- Allow coordinators to directly implement project-file changes because they
  have high provider permissions.
- Automatically decide whether a capability escalation should be approved.
- Replace the existing decision/blocker and autonomous technical-decision
  protocols.

## User Experience

When interactive Codex imports a plan or a coordinator spawns an agent, each
workstream and agent carries a profile:

```json
{
  "profile_id": "worker-standard",
  "repo_write_scope": {
    "assigned_files": [
      "scripts/dispatch_engine/status.py"
    ],
    "allowed_write_roots": [
      "scripts/dispatch_engine/",
      "tests/"
    ]
  },
  "capabilities": {
    "network_access": "none",
    "package_install": "deny",
    "dependency_resolution": "allow-existing-lockfiles",
    "docker_socket": "deny",
    "service_start": "deny",
    "test_execution": "allow-listed",
    "runtime_state_write": "report-only",
    "github_issue_create": "deny"
  },
  "validation_commands": [
    "PYTHONPATH=scripts python3 -m unittest tests.test_status"
  ],
  "escalation_policy": "decision-required"
}
```

Worker prompts show the granted profile before task instructions. Worker
reports include the profile they used, every capability they exercised, and any
blocked escalation requests. `status --json` summarizes active agent
capabilities and highlights mismatches.

If an agent needs more authority, it does not silently broaden scope. It records
a blocker or decision request with the capability, reason, risk, and proposed
validation. The coordinator or interactive Codex may only continue after a
recorded decision grants the additional capability or assigns a narrower path.

## Capability Vocabulary

The initial vocabulary should be small, explicit, and extensible:

- `network_access`: `none`, `read-only-public`, `allow-listed-hosts`,
  `unrestricted`.
- `package_install`: `deny`, `allow-dev-dependencies`, `allow-project-manager`,
  `unrestricted`.
- `dependency_resolution`: `deny`, `allow-existing-lockfiles`,
  `allow-lockfile-update`, `unrestricted`.
- `docker_socket`: `deny`, `read-only`, `build`, `unrestricted`.
- `service_start`: `deny`, `local-only`, `allow-listed`, `unrestricted`.
- `test_execution`: `deny`, `allow-listed`, `allow-project-tests`,
  `unrestricted`.
- `repo_write_scope`: assigned files and allowed write roots using the existing
  path-scope contract.
- `runtime_state_write`: `none`, `report-only`, `agent-heartbeat`,
  `coordinator`.
- `github_issue_create`: `deny`, `draft-only`, `allow-dispatch-engine`,
  `unrestricted`.

## Behavior Invariants

1. Every workstream has a requested capability profile before dispatch.
2. Every registered worker, reviewer, and validator has a granted capability
   profile in durable run state.
3. The coordinator may run with high provider permissions, but spawned agents
   still receive explicit narrower profiles.
4. Provider enforcement is advisory and provider-specific; Dispatch Engine
   validates the durable contract it can observe.
5. A report that shows capability use outside the granted profile is a protocol
   violation unless linked to a recorded approval decision.
6. Capability escalation requires a decision or blocker record before the agent
   continues with the new capability.
7. Final reports list granted capabilities, exercised capabilities, approved
   escalations, denied escalations, and capability violations.

## Acceptance Criteria

- Plan schema and examples include workstream capability profiles.
- Agent registration records include granted capability profiles.
- Worker, reviewer, and validator prompt templates render the profile in a
  clear machine-readable block.
- Agent reports include claimed exercised capabilities and escalation requests.
- Status output exposes active capability grants, pending capability
  decisions, and capability violations.
- Decision/blocker guidance describes how to request capability escalation.
- Documentation states that provider enforcement is provider-specific while the
  Dispatch Engine contract is explicit and auditable.
- Tests cover profile parsing, status summaries, report mismatch detection,
  and prompt rendering.
