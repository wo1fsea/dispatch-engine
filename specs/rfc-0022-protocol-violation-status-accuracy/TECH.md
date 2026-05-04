---
language: en-US
audience: agent
doc_type: spec
---

# Protocol Violation Status Accuracy Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #16 was partially stale after later dogfood updates. The current useful
problem is not worker-004's capability report; that report is now canonical.
The current status output still shows:

- `unregistered_implementation_completion` for workstreams whose
  `workstreams/*.json` files have `assigned_agent`, but assigned agents are
  cancelled.
- `protocol_violation` alerts with `violation: "unknown"` for historical
  event payloads that contain capability overreach fields but no explicit
  violation name.

Relevant current files:

- `scripts/dispatch_engine/agents.py`: detected protocol violations.
- `scripts/dispatch_engine/state.py`: event violation parsing and alerts.
- `tests/test_worker_adapter_protocol.py` or `tests/test_status_tail.py`.
- `references/event-protocol.md` and operator docs if semantics change.

## Change Gate

- Problem: Status/alerts use misleading labels that make dogfood issue triage
  harder.
- Existing path considered: Leave current conservative fallback names.
- Why existing path is insufficient: The user and interactive Codex cannot
  tell registered-but-invalid workstreams from truly unregistered workstreams.
- Smallest new surface: New targeted violation names and event normalization.
- What will be deleted or replaced: Replace misleading fallback behavior for
  assigned invalid agents and unknown capability event payloads.
- Owner: Dispatch Engine maintainers.
- Validation: focused protocol/status tests, full unittest discovery, dogfood
  status/alerts for #16 run id, `git diff --check`.
- Temporary or permanent: Permanent diagnostic accuracy.
- Removal condition: Superseded only by a richer status consistency subsystem.

## Proposed Changes

1. Refine workstream completion validation in `agents.py`.
   - Build implementation agents by id and workstream.
   - If `assigned_agent` exists but agent is missing, report an assigned-agent
     missing diagnostic.
   - If assigned agent exists but status is cancelled/failed/running, report a
     targeted invalid-assigned-agent diagnostic with actual status.
   - If assigned agent completed but report validation failed, keep the report
     validation diagnostics and avoid the unregistered fallback.
2. Normalize legacy `protocol.violation` event payloads in `state.py`.
   - If payload has no `violation` but contains `capability`, classify it as
     `capability_overreach` or a compatibility-specific name.
   - Preserve payload details for audit.
3. Add regression tests from the #16 shapes.
4. Update docs to describe detected violations versus event-carried violations.

## Validation Plan

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol tests.test_status_tail
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
git diff --check
```

Dogfood check:

```bash
python3 scripts/de.py status "/Users/huangquanyong/Projects/ObsidianVault/02 Engineering/Projects/Paseo Passport/paseo-passport" --run-id 20260503T180445882676Z --json
python3 scripts/de.py alerts "/Users/huangquanyong/Projects/ObsidianVault/02 Engineering/Projects/Paseo Passport/paseo-passport" --run-id 20260503T180445882676Z --json
```

## Risks

- Renaming diagnostics may affect users relying on old names. Mitigate by
  keeping `unregistered_implementation_completion` only for truly unregistered
  cases and documenting new names.
- Historical events cannot be rewritten. Mitigate through read-time
  compatibility normalization.

## Follow-ups

- Decide whether aggregate `run.json` versus per-workstream file mismatches
  need a separate lifecycle diagnostic.
