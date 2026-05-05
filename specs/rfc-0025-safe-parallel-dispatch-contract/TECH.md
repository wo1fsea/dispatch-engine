---
language: en-US
audience: agent
doc_type: spec
---

# Safe Parallel Dispatch Contract Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #22 came from the rfc-0024 dashboard dogfood run. The imported plan set
every workstream to `mode: serial`, `parallel_group: null`, and created a full
dependency chain from `04-theme-settings-keyboard` through
`10-parity-validation`. The coordinator obeyed that shape and spawned one
worker after the previous workstream completed. The run succeeded, but it did
not exercise the intended Dispatch Engine behavior: use subagents in parallel
whenever dependencies and write scopes allow it.

Relevant current files:

- `SKILL.md`: operator-level Dispatch Engine rules and operating flow.
- `references/operator-flow.md` and `references/operator-guide.md`: plan and
  run guidance for interactive Codex.
- `references/orchestrator-loop.md`: adapter-neutral loop and coordination
  rules.
- `references/prompts/coordinator-protocol.md`: coordinator launch prompt.
- `scripts/dispatch_engine/plan_schema.py`: plan validation, overlap checks,
  and capability normalization.
- `scripts/dispatch_engine/state.py`: status summaries that could expose
  read-only diagnostics if runtime support is needed.
- `tests/test_codex_facing_control_surface.py`,
  `tests/test_status_tail.py`, and focused plan-schema tests if added.

## Change Gate

- Problem: Current skill/prompt/plan guidance can make coordinator dogfood
  runs accidentally serial even when the user expects safe parallel subagents.
- Existing path considered: Let interactive Codex manually write better plans.
- Why existing path is insufficient: The same failure can recur because neither
  the skill nor the coordinator prompt requires a parallelism analysis or a
  serial-rationale report.
- Smallest new surface: Skill/reference/prompt guidance plus optional
  warning-only plan diagnostics. Do not add a scheduler first.
- What will be deleted or replaced: No existing provider-spawn or observability
  contract is replaced.
- Owner: Dispatch Engine maintainers.
- Validation: docs grep, focused prompt/plan diagnostic tests if runtime helper
  is added, full unittest discovery, CLI help smoke if CLI surface changes,
  and `git diff --check`.
- Temporary or permanent: Permanent coordinator contract.
- Removal condition: Superseded by a richer scheduler/advisor that preserves
  coordinator ownership and durable `.dispatch/` observability.

## Proposed Changes

1. Add a parallelism-analysis contract to skill and operator guidance.
   - Interactive Codex must analyze workstream independence before writing an
     explicit plan.
   - The plan should include, either in `repo_context` or a dedicated
     `parallelism` object:
     - concurrency budget;
     - safe batches or `parallel_group` labels;
     - dependency edges and their rationale;
     - write-scope conflicts;
     - planned integration/review gates;
     - intentionally serialized workstreams and rationale.
   - Broad shared write roots should be narrowed to concrete files whenever
     that makes safe parallelism possible.
2. Strengthen the coordinator prompt.
   - Before spawning, compute a ready set from imported workstreams, current
     agent state, dependencies, blockers, capability warnings, and active write
     scopes.
   - Batch-spawn all safe ready workers up to the plan's concurrency budget.
   - Record dispatch batches in `.dispatch/` events or the coordinator report.
   - Record a serial rationale for every ready workstream not spawned.
   - Keep the coordinator-only rule: no project-file implementation by the
     coordinator.
3. Clarify coordinated overlap.
   - Existing `coordination: shared-write-approved` remains the escape hatch
     for shared-file parallelism.
   - Guidance should require an integration protocol when using coordinated
     overlap: owner, merge order, conflict handling, and validation gate.
4. Add warning-only runtime diagnostics if needed.
   - Candidate helper: `plan_diagnostics` in `plan_schema.py`, surfaced by
     `de init --json` or a future `de plan-diagnostics`.
   - Warnings:
     - all workstreams are `mode: serial` with no explicit serial rationale;
     - long dependency chain with broad repeated write scopes;
     - multiple independent workstreams have no `parallel_group`;
     - broad directory write roots are used where concrete files are declared.
   - Diagnostics must not reject valid conservative plans unless existing
     overlap validation already rejects them.
5. Update docs and status expectations.
   - `specs/README.md` should list this spec.
   - Future dogfood reports should include active concurrency, planned versus
     actual batches, and any serialized-ready workstreams.

## Validation Plan

Docs/prompt-only baseline:

```bash
rg -n "parallelism|ready set|ready workstream|concurrency budget|serial rationale|parallel_group|shared-write-approved" SKILL.md references specs/rfc-0025-safe-parallel-dispatch-contract
git diff --check
```

If runtime diagnostics are added:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_plan_schema
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py init --help
git diff --check
```

Dogfood validation:

```bash
python3 scripts/de.py init . --plan .dispatch/plans/<parallel-dogfood-plan>.json
python3 scripts/de.py run . --dry-run
python3 scripts/de.py status . --json
```

The dogfood plan should contain at least two independent workstreams with
disjoint assigned files and prove the coordinator spawns them in the same
dispatch batch, or records a concrete reason why it cannot.

## Risks

- Over-aggressive parallelism can create merge conflicts or subtle UI
  regressions. Mitigate with narrower file scopes, integration workstreams,
  and explicit review gates.
- Runtime diagnostics could drift into scheduler behavior. Mitigate by keeping
  diagnostics warning-only unless the existing plan validator is already
  enforcing overlap safety.
- Provider-native spawn limits may vary. Mitigate with a plan-level concurrency
  budget and recorded provider-limit rationale.
- Requiring too much plan metadata could slow small tasks. Mitigate by letting
  one-workstream plans state "parallelism not applicable" briefly.

## Follow-ups

- Add a dashboard/status surface for planned versus actual dispatch batches if
  dogfood shows it helps supervision.
- Add an optional runtime ready-set advisor after skill/prompt guidance is
  validated in dogfood.
- Consider provider-specific default concurrency recommendations for Codex and
  Claude.
