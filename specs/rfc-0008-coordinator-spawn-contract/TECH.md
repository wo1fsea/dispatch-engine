---
language: en-US
audience: agent
doc_type: spec
---

# Coordinator Spawn Contract Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

`rfc-0006-live-coordinator-supervision` lets Dispatch Engine launch a provider CLI coordinator and record coordinator prompt/log/status state.

`rfc-0007-worker-adapter-protocol` adds helper-first worker registration, centralized worker prompts, prompt snapshots, durable worker reports, report validation, status visibility, and conservative protocol violations.

The next correction is architectural: Dispatch Engine should not assume it owns worker spawning. The coordinator may use provider-native subagent tools or CLI-specific mechanisms. Dispatch Engine needs the registration and evidence contract, not the provider-specific spawn implementation.

## Change Gate

- Problem: The next action was drifting toward a DE-owned worker launch adapter, which would steal orchestration responsibility from the coordinator.
- Existing path considered: Implement a runtime worker provider launch adapter.
- Why existing path is insufficient: It makes DE responsible for provider-specific subagent mechanics before the coordinator-spawn contract is stable.
- Smallest new surface: Update coordinator/worker protocol prompts and docs so coordinator-spawned agents must be registered and reported through rfc-0007 state.
- What will be deleted or replaced: No runtime helpers need deletion; rfc-0007 helpers remain the registration/report substrate.
- Owner: Dispatch Engine maintainers.
- Validation: prompt/doc grep, focused prompt rendering tests if prompt templates change, full unittest discovery, CLI smoke checks, and `git diff --check`.
- Temporary or permanent: Permanent architectural contract.
- Removal condition: Superseded only by a richer adapter layer that still preserves coordinator ownership of spawn decisions and `.dispatch/` observability.

## Proposed Changes

### Coordinator Prompt Contract

Update `references/prompts/coordinator-protocol.md` to state:

- The coordinator may spawn workers, reviewers, or validators using provider-native mechanisms.
- Before assigning work, the coordinator must register spawned agents in `.dispatch/runs/<run-id>/agents/`.
- The coordinator must render/write prompt snapshots under `.dispatch/runs/<run-id>/prompts/`.
- The coordinator must ensure role-specific evidence is written under `.dispatch/runs/<run-id>/reports/` for workers, `reviews/` for reviewers, and `validation/` for validators.
- The coordinator must keep `agent.spawned`, `workstream.assigned`, `agent.heartbeat`, `agent.completed`, `agent.failed`, and `protocol.violation` state current.
- The coordinator may not accept implementation evidence without a valid report.
- The coordinator must not directly implement project files to bypass the worker protocol.

### Worker Protocol Reference

Update `references/worker-protocol.md` to avoid saying workers are launched by the runtime. Workers are coordinator-spawned or adapter-spawned, but either path must use the same `.dispatch/` registration/report contract.

### Orchestrator Loop Reference

Update `references/orchestrator-loop.md` so the near-term loop is:

```text
imported plan -> DE launches coordinator -> coordinator spawns agents -> agents write reports -> DE status/tail reads .dispatch state
```

Do not add a deterministic scheduler as part of this baseline; keep spawn
decisions with the coordinator unless later dogfood proves a runtime helper is
strictly necessary.

### Runtime Helpers

No new runtime launch adapter is required for this RFC. If any helper is missing from rfc-0007, add only small state-oriented helpers. Avoid provider-specific worker launch code.

## Files

- `references/prompts/coordinator-protocol.md`
- `references/worker-protocol.md`
- `references/orchestrator-loop.md`
- `README.md`
- `SKILL.md`
- `specs/rfc-0008-coordinator-spawn-contract/STATUS.md`
- `specs/README.md`
- tests only if prompt rendering assertions need updates

## Testing and Validation

Run:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
rg "coordinator-spawn|spawned agent|agent.spawned|workstream.assigned|worker report|registered worker|provider-native" README.md SKILL.md references specs/rfc-0008-coordinator-spawn-contract
git diff --check
```

Manual checks:

- Docs no longer imply DE must own worker launch.
- Coordinator prompt requires registration before assignment.
- Worker protocol still requires durable reports before evidence is accepted.
- Runtime-generated non-project state remains under `.dispatch/`.

## Risks and Follow-ups

- Risk: Without a DE-owned worker launcher, the coordinator may spawn agents inconsistently. Mitigation: require registration/report/event state and protocol violations.
- Risk: Provider-native spawn APIs differ widely. Mitigation: keep rfc-0008 adapter-neutral.
- Follow-up: Add reviewer/validator report protocols.
- Follow-up: Add optional provider-specific spawn adapters only after dogfood shows where coordinator-native spawn is insufficient.
- Follow-up: Add stale heartbeat detection when background execution exists.
