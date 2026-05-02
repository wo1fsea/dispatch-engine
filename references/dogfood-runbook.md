---
language: en-US
audience: agent
doc_type: runbook
---

# Dogfood Runbook

Use this runbook to demonstrate Dispatch Engine with its own skill-first,
runtime-when-necessary workflow. It is a deterministic smoke path, not a new
scheduler and not a replacement for provider-native coordinator judgment.

## Fixture

The plan fixture lives at:

```text
fixtures/dogfood-runbook/plan.json
```

Import it into the target repository. The plan source may live in the project
tree, but all generated run state must be written under the target repository's
`.dispatch/` directory.

```bash
python3 scripts/de.py init . --plan fixtures/dogfood-runbook/plan.json --json
```

Record the returned `run_id` before continuing.

## Coordinator Shapes

Render the coordinator launch without writing runtime state:

```bash
python3 scripts/de.py run . --run-id <run-id> --dry-run --json
python3 scripts/de.py run . --run-id <run-id> --provider claude --dry-run --json
```

For a live-form smoke, put a deterministic executable named `codex` or `claude`
earlier on `PATH` and run:

```bash
python3 scripts/de.py run . --run-id <run-id> --provider codex --json
```

The live-form smoke should register `coordinator-001`, write the coordinator
prompt and logs under `.dispatch/runs/<run-id>/`, and emit coordinator lifecycle
events. It does not need to call a real provider.

## Evidence Loop

Use existing runtime helpers or equivalent coordinator actions to register:

- a worker for `01-dogfood-evidence-loop`
- a reviewer for the same workstream
- a validator for the same workstream

Each spawned implementation agent must write durable evidence under the run:

```text
.dispatch/runs/<run-id>/agents/
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/reviews/
.dispatch/runs/<run-id>/validation/
.dispatch/runs/<run-id>/heartbeats/
```

Worker reports should include changed files, validation attempts, questions,
blockers, and risks. Reviewer reports should follow
`references/review-validator-protocol.md`. Validator reports should record the
command, output summary, and artifact paths, or an explicit skipped reason.

## Status And Tail

Query the durable state:

```bash
python3 scripts/de.py status . --run-id <run-id> --json
python3 scripts/de.py tail . --run-id <run-id> --json
```

Expected minimum signals:

- the imported plan has one workstream
- coordinator, worker, reviewer, and validator agents are visible
- heartbeats are counted
- tail includes plan import, coordinator lifecycle, agent lifecycle, decision,
  and blocker events
- unresolved blockers are reflected in status until resolved

## Decision And Blocker Records

Record decisions and blockers when the run needs operator judgment. Append
records instead of rewriting history:

```text
.dispatch/runs/<run-id>/decisions.jsonl
.dispatch/runs/<run-id>/blockers.jsonl
```

Resolve them once the operator chooses a path. Pending decisions and unresolved
blockers are intentionally visible through status so the coordinator can pause
or resume with durable context.

## Validation

The deterministic fixture smoke is covered by:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dogfood_runbook_fixture
```

Full regression:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
```
