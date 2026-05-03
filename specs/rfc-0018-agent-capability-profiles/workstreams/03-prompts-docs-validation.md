---
workstream_id: 03-prompts-docs-validation
spec_id: rfc-0018-agent-capability-profiles
language: en-US
audience: agent
doc_type: workstream
status: planned
owner: unassigned
updated: 2026-05-03
depends_on:
  - 01-capability-contract
  - 02-status-and-decision-surfacing
---

# Prompts Docs Validation

## Scope

Update the skill-first guidance, prompt templates, operator docs, and validation
coverage so coordinators and spawned agents consistently understand capability
profiles. This workstream also records the provider-enforcement boundary:
Dispatch Engine defines the auditable contract; providers may enforce pieces of
it in provider-specific ways.

## Tasks

- Update coordinator, worker, reviewer, and validator prompt templates to
  include capability profile blocks and escalation rules.
- Update skill and reference docs to distinguish RFC-0017 coordinator
  high-permission launch from narrower spawned-agent capability grants.
- Update decision/blocker guidance with capability escalation examples.
- Update worker/reviewer/validator report guidance with exercised capability
  and escalation fields.
- Document provider-specific enforcement as optional translation of the
  Dispatch Engine profile, not the source of truth.
- Add fixture plans and reports that demonstrate standard, dependency, validator,
  reviewer, and issue-reporter profiles.
- Add dogfood validation notes that cover Alpha Kitchen style non-file
  capability pressure.
- Keep all examples explicit about network access, package installs, dependency
  resolution, Docker socket/service starts, test execution, repo write scope,
  runtime state writes, and GitHub issue creation.

## Acceptance

- Prompt snapshots show capability grants before task instructions.
- Docs describe what an agent should do when it needs a denied capability.
- Report examples include `capabilities_exercised` and
  `capability_escalations`.
- Guidance states that agents stop and request a decision before broadening
  capability scope.
- Search across docs and prompts finds all initial vocabulary terms.
- Full test discovery and diff checks pass after implementation.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles
PYTHONPATH=scripts python3 -m unittest discover -s tests
rg -n "capability_profile|network_access|package_install|dependency_resolution|docker_socket|service_start|test_execution|runtime_state_write|github_issue_create|capability.escalation" SKILL.md README.md references specs/rfc-0018-agent-capability-profiles
git diff --check
```
