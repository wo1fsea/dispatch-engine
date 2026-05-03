---
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: agent
doc_type: status
status: ready-for-implementation
implementation: planned
validation: not-run
coordinator: dispatch-engine
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/1
---

# Status

## Summary

Planned and ready for implementation. This spec defines explicit Dispatch
Engine capability profiles for workstreams and agents so non-file authority is
visible, reviewable, and auditable. The coordinator high-permission launch
baseline from RFC-0017 remains unchanged; this work defines the narrower
profile contract for workers, reviewers, validators, escalation decisions,
status summaries, prompts, reports, docs, and validation.

No runtime, prompt, reference, or documentation changes outside this RFC
directory have been implemented yet.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01-capability-contract | Profile schema, presets, plan import, agent registration, report validation | planned | unassigned | TBD | rfc-0017 | 2026-05-03 |
| 02-status-and-decision-surfacing | Status summaries, events, pending escalation decisions, violations | planned | unassigned | TBD | 01-capability-contract, rfc-0011, rfc-0016 | 2026-05-03 |
| 03-prompts-docs-validation | Prompt templates, skill/reference docs, validation coverage, dogfood notes | planned | unassigned | TBD | 01-capability-contract, 02-status-and-decision-surfacing | 2026-05-03 |

## Acceptance Criteria

- Workstreams and registered agents have explicit normalized capability
  profiles in durable state.
- Existing repo write scope remains part of the profile and continues to be
  validated.
- Coordinator high-permission behavior from RFC-0017 is preserved and
  documented as distinct from spawned-agent profiles.
- Agent prompt snapshots render granted capabilities and escalation rules.
- Agent reports declare exercised capabilities and requested escalations.
- Capability overreach is surfaced as a protocol violation unless linked to an
  approving decision.
- `status --json` exposes active profiles, high-risk grants, pending
  escalations, and capability violations.
- Decision/blocker guidance explains how to request, approve, deny, and audit
  capability escalation.
- Provider enforcement remains provider-specific, while the Dispatch Engine
  contract is explicit and auditable.

## Planned Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py init --help
python3 scripts/de.py status --help
rg -n "capability_profile|network_access|package_install|dependency_resolution|docker_socket|service_start|runtime_state_write|github_issue_create" SKILL.md README.md references specs/rfc-0018-agent-capability-profiles
git diff --check
```

Validation has not been run because this task only creates the spec.
