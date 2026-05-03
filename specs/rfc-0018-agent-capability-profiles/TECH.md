---
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: agent
doc_type: spec
status: planned
created: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/1
---

# Agent Capability Profiles Tech Spec

## Design

Dispatch Engine should add a first-class capability profile model that sits
beside the existing assigned-file and allowed-write-root model. The runtime
does not become a provider-independent sandbox. Instead, it records requested
and granted capability profiles, renders them into prompts, requires reports to
declare actual capability use, and surfaces mismatches as auditable protocol
state.

RFC-0017 remains the coordinator launch baseline. Coordinators keep high
provider permissions so they can inspect, spawn, install, validate, and recover
runs. The coordinator-only boundary still applies: coordinators write
Dispatch Engine state under `.dispatch/` and delegate project-file changes to
registered agents. This spec extends that delegation with capability profiles.

## Data Model

Add a versioned capability profile object wherever workstream and agent scope is
stored.

```json
{
  "schema_version": 1,
  "profile_id": "worker-standard",
  "summary": "Project-file edits plus listed tests; no network or services.",
  "repo_write_scope": {
    "assigned_files": [],
    "allowed_write_roots": []
  },
  "capabilities": {
    "network_access": {
      "mode": "none",
      "allowlist": []
    },
    "package_install": {
      "mode": "deny",
      "managers": []
    },
    "dependency_resolution": {
      "mode": "allow-existing-lockfiles"
    },
    "docker_socket": {
      "mode": "deny"
    },
    "service_start": {
      "mode": "deny",
      "allowlist": []
    },
    "test_execution": {
      "mode": "allow-listed",
      "commands": []
    },
    "runtime_state_write": {
      "mode": "report-only"
    },
    "github_issue_create": {
      "mode": "deny",
      "repositories": []
    }
  },
  "escalation_policy": {
    "mode": "decision-required",
    "allowed_autonomous_technical": false
  }
}
```

The compact string shape in product examples is acceptable for author-facing
docs, but runtime records should normalize to object values so allowlists and
future metadata do not require schema churn.

## Profile Presets

Provide named presets to reduce prompt noise while keeping the full normalized
profile in run state.

- `coordinator-baseline`: high provider permission process, Dispatch
  Engine `.dispatch/` writes, may spawn agents and request decisions; not a
  project-file implementation profile.
- `worker-readonly`: inspect and report only; no repository writes.
- `worker-standard`: assigned project writes, listed tests, no network,
  installs, Docker, services, runtime writes beyond final report.
- `worker-dependency`: assigned project writes plus dependency resolution or
  package manager actions approved by the plan.
- `validator-standard`: no project writes, listed validation commands,
  read-only report writes under `.dispatch/`.
- `reviewer-standard`: no project writes, read-only inspection, review evidence
  writes under `.dispatch/`.
- `issue-reporter`: no project writes; may draft or create GitHub issues only
  under the approved repository and reporting protocol.

Presets are defaults, not hidden authority. The normalized granted profile must
be written into agent state and prompt snapshots.

## Runtime Surfaces

### Plan Import

Plan workstreams should accept `capability_profile` in addition to assigned
files, allowed write roots, and validation expectations. If omitted, importer
defaults are conservative:

- implementation workers: `worker-standard`
- reviewers: `reviewer-standard`
- validators: `validator-standard`

The importer should reject unknown capability keys, unknown mode values, and
profile objects that omit repo write scope.

### Agent Registration

Agent registry records should include:

```json
{
  "agent_id": "worker-001",
  "role": "worker",
  "capability_profile": {},
  "capability_profile_source": "workstream",
  "capability_profile_decision_ids": []
}
```

When a decision expands capability scope, append the decision id and write the
updated granted profile. Keep prior event history append-only.

### Prompt Rendering

Prompt templates for workers, reviewers, and validators must render:

- profile id and summary
- repo write scope
- capability modes and allowlists
- validation commands
- escalation policy
- instruction to stop and request a blocker/decision when work requires a
  denied capability

Provider-specific launch adapters may translate a profile into native flags
where possible, but the prompt snapshot is the Dispatch Engine source of truth.

### Reports

Agent reports should include:

```json
{
  "capability_profile_id": "worker-standard",
  "capabilities_exercised": [
    {
      "capability": "test_execution",
      "mode": "allow-listed",
      "evidence": "Ran listed unittest command."
    }
  ],
  "capability_escalations": [
    {
      "capability": "network_access",
      "requested_mode": "read-only-public",
      "status": "blocked",
      "decision_id": "decision-002",
      "reason": "Needed upstream package docs."
    }
  ]
}
```

Report validation should compare exercised capabilities to the granted profile
and emit protocol violations for overreach. For capabilities the runtime cannot
directly observe, the report remains self-attestation plus review evidence; the
contract is still auditable.

### Status And Events

`status --json` should include a compact capability summary:

```json
{
  "capability_profiles": {
    "agents": [
      {
        "agent_id": "worker-001",
        "role": "worker",
        "profile_id": "worker-standard",
        "high_risk_capabilities": [],
        "pending_escalations": []
      }
    ],
    "pending_decisions": [
      {
        "decision_id": "decision-002",
        "capability": "network_access",
        "requested_mode": "read-only-public"
      }
    ],
    "violations": []
  }
}
```

New or extended event types should cover:

- `capability.profile.granted`
- `capability.escalation.requested`
- `capability.escalation.resolved`
- `capability.violation`

## Escalation Contract

Capability escalation is a decision/blocker specialization:

1. Agent stops before using the denied capability.
2. Agent records the required capability, requested mode, reason, risk, and
   validation expectation in its report or heartbeat.
3. Coordinator records a decision or blocker in `.dispatch/`.
4. Interactive Codex or the coordinator resolves the decision according to the
   existing decision protocol.
5. If approved, the coordinator updates the agent profile, records the decision
   id, and resumes or respawns the agent.
6. If denied, the workstream is narrowed, reassigned, or marked blocked.

Autonomous technical-decision fallback from RFC-0016 may apply only when the
capability escalation is conservative, reversible, inside the approved
objective, and excludes product, security/privacy, deployment, credentials,
destructive data, legal/financial, and business-scope categories.

## Validation

Implementation should add or update tests for:

- profile normalization and importer defaults
- unknown capability and invalid mode rejection
- prompt rendering with capability blocks
- agent registration with granted profiles
- report validation for exercised capabilities outside the grant
- status summaries for active profiles, pending escalations, and violations
- decision-linked profile expansion

Suggested validation commands:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py init --help
rg -n "capability_profile|network_access|package_install|github_issue_create|capability.escalation" SKILL.md README.md references specs/rfc-0018-agent-capability-profiles
git diff --check
```
