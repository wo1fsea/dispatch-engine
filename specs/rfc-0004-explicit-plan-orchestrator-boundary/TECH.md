---
language: en-US
audience: agent
doc_type: spec
---

# Explicit Plan Orchestrator Boundary Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Runtime shape before this spec, after `rfc-0003-runtime-state-and-tail`:

- `scripts/de.py` is the bundled CLI entrypoint.
- `scripts/dispatch_engine/cli.py` exposes `version`, `inspect`, `plan`, `status`, and `tail`.
- `scripts/dispatch_engine/inspect.py` scans the target repository for instructions, planning sources, and validation hints.
- `scripts/dispatch_engine/planner.py` accepts an objective and heuristically creates workstreams and pending decisions.
- `scripts/dispatch_engine/runs.py`, `state.py`, and `events.py` provide durable `.dispatch/runs/<run-id>/` state and readers.
- `tests/test_inspect_plan.py` validates the now-wrong runtime-owned inspect/plan behavior.
- `SKILL.md`, `README.md`, and `references/operator-flow.md` still instruct operators to run `inspect` and `plan`.

The durable run-state pieces remain useful. The runtime-owned repository understanding does not match the intended architecture.

Implemented runtime shape after this spec:

- `scripts/dispatch_engine/cli.py` exposes `version`, `init`, `status`, and `tail`.
- `scripts/dispatch_engine/plan_schema.py` validates and imports explicit dispatch plans.
- `scripts/dispatch_engine/inspect.py` and `scripts/dispatch_engine/planner.py` are removed.
- `tests/test_removed_inspect_plan.py` asserts the old commands are not advertised and do not create `.dispatch/` state.
- Status and tail coverage now uses imported explicit plans instead of heuristic planner output.

## Change Gate

- Problem: Runtime-owned `inspect` and heuristic `plan` move repository understanding into the wrong layer and create false confidence.
- Existing path considered: Keep `inspect` and `plan` as lightweight helpers.
- Why existing path is insufficient: The runtime cannot reliably infer target repository norms, accepted spec formats, validation weight, or safe workstream decomposition without Codex's interactive context and judgment.
- Smallest new surface: Define an explicit plan contract, add `de init --plan <path>`, route generated runtime files under `.dispatch/`, and remove/deprecate `inspect` plus heuristic `plan`.
- What will be deleted or replaced: Replace `inspect` and `plan --objective` with Codex-owned discovery and explicit plan import. Replace docs that direct operators to runtime inspection.
- Owner: Dispatch Engine maintainers.
- Validation: Unit tests for plan validation/import/state creation, CLI smoke tests, documentation grep checks proving the old flow is gone, and manual `.dispatch/` write-location checks.
- Temporary or permanent: Permanent boundary for the skill/runtime architecture.
- Removal condition: Superseded only if Dispatch Engine becomes an integrated Codex-native orchestration primitive with equivalent interactive context access.

## Proposed Boundary

### Interactive Codex + Skill Owns

- Read target repository instructions and local norms.
- Ask the user clarifying questions when the objective or risk is ambiguous.
- Decide whether work is serial, parallel, or blocked.
- Create the explicit dispatch plan from target repo conventions.
- Review subagent results and decide acceptance.
- Keep the user interactively informed.

### Runtime Owns

- Store generated non-project runtime content under `.dispatch/`.
- Import explicit dispatch plans into run state.
- Maintain run, workstream, decision, artifact, and event files.
- Report status and event tails.
- Later, run a mechanical orchestrator loop from the imported plan.
- Later, launch worker/reviewer adapters using prompts derived from the imported plan.

### Runtime Must Not Own

- Repository convention discovery.
- Spec-format selection.
- Workstream splitting from raw objective text.
- Validation command inference from broad file scans.
- Pending decisions invented from objective keywords.

## `.dispatch/` Storage Contract

Dispatch Engine-generated non-project content in a target repository must live under:

```text
.dispatch/
  plans/
    <plan-id>.json
  runs/
    <run-id>/
      run.json
      events.jsonl
      decisions.jsonl
      workstreams/
      artifacts/
      reviews/
      validation/
```

Examples of non-project runtime content:

- generated dispatch plans;
- run state;
- event and decision logs;
- worker prompt snapshots;
- worker/reviewer reports;
- validation command output captured by the runtime;
- temporary orchestration files.

Examples of project content that must stay outside `.dispatch/`:

- source code;
- tests;
- docs accepted into the target repo;
- repo-native specs;
- configuration files changed to satisfy the objective.

## Dispatch Plan Contract

Add a JSON plan contract. A generated plan should be written to `.dispatch/plans/<plan-id>.json` before import when the skill creates it inside the target repository.

Minimal shape:

```json
{
  "schema_version": 1,
  "plan_id": "20260502-explicit-plan",
  "objective": "Implement the requested change",
  "created_by": "interactive-codex",
  "created_at": "2026-05-02T00:00:00Z",
  "target_repo": "/absolute/path/to/repo",
  "repo_context": {
    "instructions_read": ["AGENTS.md"],
    "planning_basis": "Short human-authored summary of repo norms.",
    "validation_strategy": "Short summary of intended checks."
  },
  "workstreams": [
    {
      "id": "01-contract",
      "title": "Define explicit plan contract",
      "mode": "serial",
      "scope": "Files and behavior owned by this workstream.",
      "files": ["scripts/dispatch_engine/cli.py"],
      "depends_on": [],
      "parallel_group": null,
      "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"]
    }
  ],
  "decisions": [],
  "review": {
    "required": true,
    "strategy": "Coordinator reviews worker diffs and validation evidence before acceptance."
  }
}
```

Validation rules:

- `schema_version`, `plan_id`, `objective`, and non-empty `workstreams` are required.
- Workstream ids must be unique.
- `depends_on` entries must reference existing workstreams.
- Parallel workstreams must not declare overlapping write scopes unless the plan explicitly marks the overlap as coordinated.
- The runtime may validate structure and dependencies, but must not fill missing repository context by scanning the repo.

## CLI Changes

Add:

```bash
python3 scripts/de.py init <repo> --plan .dispatch/plans/<plan-id>.json
python3 scripts/de.py init <repo> --plan .dispatch/plans/<plan-id>.json --json
```

Behavior:

- Validate the supplied plan.
- Create `.dispatch/runs/<run-id>/`.
- Copy normalized plan metadata into `run.json`.
- Create per-workstream state files from plan workstreams.
- Create `decisions.jsonl`, `events.jsonl`, `artifacts/`, `reviews/`, and `validation/`.
- Emit `run.created` and `plan.imported`.
- Preserve `status` and `tail` readers.

Removed:

```bash
python3 scripts/de.py inspect <repo>
python3 scripts/de.py plan <repo> --objective "<objective>"
```

The implementation removes these commands from normal CLI help. Invoking them exits through argparse invalid-choice handling and does not create `.dispatch/` state.

## Documentation Changes

Update:

- `SKILL.md`: describe Codex-owned discovery and explicit plan import; remove `inspect` and heuristic `plan` examples.
- `references/operator-flow.md`: rewrite around interactive Codex producing a plan, then runtime import/status/tail.
- `references/event-protocol.md`: document `.dispatch/plans/`, `plan.imported`, `reviews/`, and `validation/`.
- `references/worker-protocol.md`: clarify workers receive workstream prompts from imported plans.
- `README.md`: remove old smoke flow and document the corrected MVP boundary.
- `specs/rfc-0003-runtime-state-and-tail/STATUS.md`: add a supersession note for the inspect/plan workstream.

## Workstream Sequencing

This spec is intentionally split so implementation can be serial or partly parallel:

- `01-boundary-docs`: documentation and skill flow correction. Can run in parallel with schema design.
- `02-plan-schema-init`: plan contract, validation, and `de init --plan`. Blocks old command removal.
- `03-remove-inspect-plan`: remove/deprecate old runtime-owned discovery/planning. Depends on `02`.
- `04-orchestrator-loop-design`: document future main orchestrator, worker, and reviewer loop. Can run in parallel after `01`.
- `05-validation`: full validation, grep checks, status updates, and handoff. Depends on all implementation workstreams.

## Testing and Validation

Run:

```bash
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py init . --plan .dispatch/plans/<plan-id>.json
python3 scripts/de.py init . --plan .dispatch/plans/<plan-id>.json --json
python3 scripts/de.py status .
python3 scripts/de.py tail .
PYTHONPATH=scripts python3 -m unittest discover -s tests
```

Manual checks:

- Generated non-project runtime files are only under `.dispatch/`.
- `.dispatch/` remains git-ignored.
- Old `inspect` and `plan --objective` docs are gone or explicitly marked as removed/migration-only.
- Invalid plans fail clearly.
- A plan with serial dependencies imports in dependency order.
- A plan with unsafe parallel overlap fails or is reported as requiring coordinator confirmation.

## Risks and Follow-ups

- Risk: Removing `inspect` and `plan` discards tests just added in `rfc-0003`. Mitigation: replace them with plan-contract tests in the same implementation wave.
- Risk: The explicit plan schema becomes too rigid. Mitigation: keep required fields minimal and allow repo-specific metadata.
- Risk: Users expect the runtime to do everything. Mitigation: docs must state the runtime is deterministic infrastructure while Codex remains the interactive reasoning layer.
- Follow-up: Implement `de run` as the main orchestrator loop after import is stable.
- Follow-up: Add adapter-specific worker launchers only after the event protocol captures review and validation outcomes.
