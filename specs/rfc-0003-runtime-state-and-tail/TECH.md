---
language: en-US
audience: agent
doc_type: spec
---

# Runtime State And Tail Tech Spec

Product spec: `./PRODUCT.md`

## Context

Dispatch Engine is now a runtime-backed skill. The bundled runtime currently supports:

- `python scripts/de.py --help`
- `python scripts/de.py version`
- `python scripts/de.py inspect <repo>`
- `python scripts/de.py plan <repo> --objective "<text>"`
- `python scripts/de.py status <repo>`

Current implementation shape:

- `scripts/de.py` is the CLI entrypoint.
- `scripts/dispatch_engine/cli.py` defines commands and output formatting.
- `scripts/dispatch_engine/inspect.py` discovers instructions, planning sources, and validation hints.
- `scripts/dispatch_engine/planner.py` writes `run.json` and `events.jsonl`.
- `scripts/dispatch_engine/state.py` reads the latest run summary.
- `references/event-protocol.md` currently documents only `run.json` and `events.jsonl`.

The next dogfood step should make run state richer before worker execution exists. This gives interactive Codex a stable control surface for future implementation.

## Change Gate

- Problem: The current runtime can create a minimal dry-run plan, but it does not expose enough durable state for interactive supervision or future worker execution.
- Existing path considered: Keep all workstream data embedded in `run.json` and print the one-line `status` summary.
- Why existing path is insufficient: Future workers, reviewers, decisions, and validation need independent append-only logs and per-workstream state files.
- Smallest new surface: Add `decisions.jsonl`, `workstreams/*.json`, `artifacts/`, `tail`, optional `--run-id` for status/tail, and richer status output.
- What will be deleted or replaced: Replace the current one-line status-only behavior with structured run summary output. Keep `run.json` for compatibility.
- Owner: Dispatch Engine maintainers.
- Validation: CLI smoke tests for help, version, inspect, plan, status, tail, missing-run behavior, explicit run id, and JSON output where applicable.
- Temporary or permanent: Permanent runtime surface for the file-based MVP.
- Removal condition: Replace only if a documented database-backed state store supersedes file state while preserving operator-equivalent commands.

## Proposed Changes

### Runtime State Layout

Create this shape during `plan`:

```text
.dispatch/
  runs/
    <run-id>/
      run.json
      events.jsonl
      decisions.jsonl
      workstreams/
        01-implementation.json
      artifacts/
```

`run.json` should include:

- `run_id`
- `repo_root`
- `objective`
- `status`
- `created_at`
- `updated_at`
- `state_dir`
- `workstreams`
- `decisions`

Each `workstreams/*.json` file should include:

- `id`
- `title`
- `scope`
- `files`
- `depends_on`
- `status`
- `validation`
- `created_at`
- `updated_at`

`decisions.jsonl` should exist even when empty.

### Event Protocol

Append at least these event types:

- `run.created`
- `workstream.planned`
- `decision.created`

Keep `plan.created` only if needed for compatibility, but prefer `run.created` as the clearer event type.

Update `references/event-protocol.md` to document the expanded state shape and initial event types.

### CLI Surface

Add:

```bash
python scripts/de.py tail <target>
python scripts/de.py status <target> --run-id <run-id>
python scripts/de.py tail <target> --run-id <run-id>
```

Do not add `--follow` yet unless it is trivial and well-tested. The MVP tail can print existing events and exit.

### Status Output

Human output should include:

- latest or selected run id
- objective
- run status
- workstream counts by status
- pending decision count
- state directory

JSON output should expose the same data as fields.

### Inspect Cleanup

Improve `inspect` by:

- avoiding duplicate planning-source output
- keeping the default planning source list bounded
- preferring high-signal planning files before broad docs
- preserving `--json` output compatibility

### Plan Decision Heuristic

Keep one workstream by default.

Create a pending decision when objective text suggests multiple domains or higher risk, such as:

- UI plus backend/API
- migration or schema change
- auth, permissions, security, billing
- worker adapter or event protocol change
- explicit request for parallel agents

For this spec, the heuristic can be simple and conservative. It should avoid pretending to understand too much.

## Touched Files or Modules

- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/planner.py`
- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/inspect.py`
- optional new module: `scripts/dispatch_engine/events.py`
- optional new module: `scripts/dispatch_engine/runs.py`
- `references/event-protocol.md`
- `README.md` only if CLI examples change materially

## Testing and Validation

Run these commands:

```bash
python scripts/de.py --help
python scripts/de.py version
python scripts/de.py inspect .
python scripts/de.py inspect . --json
python scripts/de.py plan . --objective "smoke test objective"
python scripts/de.py status .
python scripts/de.py tail .
python scripts/de.py status . --json
python scripts/de.py tail . --json
```

Manual checks:

- Confirm `.dispatch/` is ignored by git.
- Confirm generated run state contains `run.json`, `events.jsonl`, `decisions.jsonl`, `workstreams/`, and `artifacts/`.
- Confirm `tail` and `status` work when no run exists by testing in a temporary empty directory.
- Confirm an explicit missing run id returns a clear message.

## Risks and Follow-ups

- Risk: File-state shape may churn as workers are added. Mitigation: keep MVP JSON simple and document the event protocol.
- Risk: Broad inspect heuristics could produce noisy output. Mitigation: cap default lists and keep full detail available through JSON later if needed.
- Risk: Decision heuristics could block too often. Mitigation: keep them advisory and easy for an operator to resolve.
- Follow-up: Add worker execution after state, status, and tail are reliable.
- Follow-up: Add tests once a test harness exists.
