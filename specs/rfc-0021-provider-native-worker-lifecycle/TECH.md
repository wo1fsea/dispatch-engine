---
language: en-US
audience: agent
doc_type: spec
---

# Provider-Native Worker Lifecycle Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issues:

- #15: lifecycle diagnostics ignored provider-native spawn evidence fields.
- #18: provider-native worker spawn could remain pending initialization with no
  report, leaving the operator with an active-looking run and little recovery
  guidance.

Relevant current files:

- `scripts/dispatch_engine/state.py`: lifecycle diagnostics, alerts, next
  actions, launch evidence checks.
- `scripts/dispatch_engine/agents.py`: agent records, report paths, validation.
- `references/prompts/coordinator-protocol.md`: coordinator launch evidence
  guidance.
- `references/operator-guide.md` and `references/heartbeat-observation.md`:
  status and heartbeat operator behavior.
- `tests/test_status_tail.py`: lifecycle/status regression tests.

## Change Gate

- Problem: Provider-native workers can have valid spawn evidence that the
  runtime ignores, and can remain active without a report without a targeted
  lifecycle diagnostic.
- Existing path considered: Require all coordinators to write only
  `provider_native_agent_id`.
- Why existing path is insufficient: Dogfood state already contains nested
  launch evidence; status readers need compatibility to supervise existing
  runs.
- Smallest new surface: Extend lifecycle diagnostics and docs. No new CLI
  command.
- What will be deleted or replaced: Replace the narrow launch-evidence check
  and generic missing-launch summary.
- Owner: Dispatch Engine maintainers.
- Validation: focused lifecycle tests, full unittest discovery, CLI smoke, and
  dogfood status checks for #15/#18 run ids.
- Temporary or permanent: Permanent compatibility and diagnostic behavior.
- Removal condition: Superseded by a richer provider adapter that still
  preserves these status semantics.

## Proposed Changes

1. Normalize launch evidence in `state.py`.
   - Add a helper that returns structured launch evidence items.
   - Recognize canonical top-level fields and nested `launch_evidence` /
     `provider_launch.evidence` fields.
   - Treat stdout/stderr as evidence only when the referenced file exists.
2. Improve `missing_agent_launch_evidence`.
   - Include accepted evidence fields in diagnostic details.
   - Avoid saying stdout/stderr are absent when they are present but missing on
     disk.
3. Add `provider_spawn_without_report` or equivalent lifecycle diagnostic.
   - Applies to active worker/reviewer/validator records with provider-native
     launch evidence and missing role-specific report file.
   - Should be material and appear in `alerts --json`.
   - Should contribute to non-terminal `next_actions`.
4. Update coordinator/operator/heartbeat docs.
   - Canonical field is `provider_native_agent_id`.
   - Runtime also recognizes compatibility fields from dogfood runs.
   - Active provider-native spawn without report is operator-visible and should
     be repaired, blocked, failed, or cancelled.

## Validation Plan

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
git diff --check
```

Dogfood checks:

```bash
python3 scripts/de.py status "/Users/huangquanyong/Projects/ObsidianVault/02 Engineering/Projects/Agent Blackboard/agent-blackboard" --run-id 20260503T180517926231Z --json
python3 scripts/de.py status "/Users/huangquanyong/Projects/ObsidianVault/02 Engineering/Projects/Paseo Passport/paseo-passport" --run-id 20260503T183631153640Z --json
```

## Risks

- Too aggressive no-report diagnostics could create noise for fresh workers.
  Mitigate with a conservative staleness threshold and tests.
- Compatibility evidence recognition could hide truly fake launches. Mitigate
  by still requiring provider spawn ids, pid, or existing log files.

## Follow-ups

- A future provider adapter can poll provider-native pending-init/running/failed
  state directly.
