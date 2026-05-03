---
workstream_id: 01-capability-contract
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: agent
doc_type: workstream
status: planned
owner: unassigned
updated: 2026-05-03
depends_on:
  - rfc-0017
---

# Capability Contract

## Scope

Implement the core capability profile contract for workstreams and registered
agents. This workstream owns schema, normalization, conservative defaults,
profile presets, plan import, agent registration, prompt/report data plumbing,
and protocol violation detection for declared overreach.

## Tasks

- Add a normalized `capability_profile` model with schema version, profile id,
  summary, repo write scope, capability modes, allowlists, validation commands,
  and escalation policy.
- Define built-in presets for coordinator baseline, readonly worker, standard
  worker, dependency worker, reviewer, validator, and issue reporter.
- Extend plan import so each workstream can request a capability profile.
- Default omitted worker/reviewer/validator profiles to conservative presets.
- Reject unknown capability keys and invalid mode values during import or
  registration.
- Store granted profiles in agent registry records and prompt snapshots.
- Extend agent report schema with `capabilities_exercised` and
  `capability_escalations`.
- Compare exercised capabilities against grants and emit protocol violations
  for overreach without an approving decision id.
- Preserve existing assigned files and allowed write roots validation.

## Acceptance

- Every imported workstream has a requested profile after normalization.
- Every registered worker, reviewer, and validator has a granted profile in
  durable run state.
- Repo write scope remains mandatory inside the profile.
- Worker reports can declare exercised capabilities and blocked escalation
  requests.
- Mismatched exercised capabilities produce a protocol violation with agent id,
  capability, requested mode, granted mode, and evidence path.
- Coordinator records continue to show `.dispatch/` write authority only, even
  though provider launch permissions remain high per RFC-0017.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```
