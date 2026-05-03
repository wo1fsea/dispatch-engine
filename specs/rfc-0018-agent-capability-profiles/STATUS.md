---
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: agent
doc_type: status
status: implemented
implementation: first-pass-complete
validation: passed
coordinator: dispatch-engine
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/1
---

# Status

## Summary

First practical implementation is complete. Dispatch Engine now normalizes
workstream and agent `capability_profile` records, stores granted profiles in
agent state, renders profile blocks in worker/reviewer/validator prompts,
accepts report `capabilities_exercised` and `capability_escalations`, detects
reported overreach without a decision id, and exposes `status --json`
`capability_profiles` summaries.

Provider enforcement remains provider-specific. This implementation records the
auditable Dispatch Engine contract in state, prompts, reports, events, status,
and docs; it does not implement a provider-independent sandbox.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01-capability-contract | Profile schema, presets, plan import, agent registration, report validation | implemented | Codex | local | rfc-0017 | 2026-05-03 |
| 02-status-and-decision-surfacing | Status summaries, events, pending escalation decisions, violations | implemented-first-pass | Codex | local | 01-capability-contract, rfc-0011, rfc-0016 | 2026-05-03 |
| 03-prompts-docs-validation | Prompt templates, skill/reference docs, validation coverage, dogfood notes | implemented-first-pass | Codex | local | 01-capability-contract, 02-status-and-decision-surfacing | 2026-05-03 |

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

## Remaining Risks / Gaps

- Decision-linked profile expansion is auditable by decision id in reports, but
  there is no dedicated helper yet that mutates an existing agent grant after a
  decision resolution.
- Capability escalation currently surfaces through pending decision records and
  report `capability_escalations`; full blocker specialization and automatic
  escalation resolution summaries remain future work.
- Runtime overreach detection is report-based self-attestation plus review
  evidence. Provider-native enforcement translation is intentionally outside
  this first pass.
- `capability.profile.granted` is emitted by the worker registration helper;
  generic reviewer/validator coordinator spawns can emit the helper event when
  they perform registration.

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

Focused validation passed during implementation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_agent_state_protocol
```

Final validation passed before handoff:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest tests.test_review_validator_protocol
PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py init --help
python3 scripts/de.py status --help
git diff --check
```
