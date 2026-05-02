---
language: en-US
audience: agent
doc_type: normative
---

# Worker Protocol

Use this reference when changing worker or reviewer adapters.

## Source Of Truth

Workers and reviewers are launched from imported dispatch plan state, not from a fresh runtime repository scan. Interactive Codex plus the skill prepares the plan; the runtime turns each imported workstream into adapter-neutral worker and reviewer prompts.

Generated worker prompts, reports, review records, and validation captures are non-project runtime content and stay under `.dispatch/runs/<run-id>/`.

Provider CLI processes launched through `de run` are coordinators, not
implementation agents. A coordinator may plan, dispatch, monitor, review,
summarize, request decisions, and write `.dispatch/` runtime state. It must not
directly implement project-file changes. Project implementation must be done by
registered workers, reviewers, or validators.

## Coordinator Launch

The current coordinator launch surface is dry-run rendering:

```bash
python3 scripts/de.py run <repo> --dry-run
python3 scripts/de.py run <repo> --provider codex --dry-run
python3 scripts/de.py run <repo> --provider claude --dry-run
```

Omitting `--provider` defaults to provider `codex`. Provider `codex` renders a
`codex exec` command shape; provider `claude` renders a `claude -p` command
shape. Dry-run renders the command and coordinator prompt without launching the
provider process.

## Agent Registration

Workers, reviewers, and validators must be registered in
`.dispatch/runs/<run-id>/agents/` before their output is accepted. Their
reports, logs, and heartbeat streams belong under:

```text
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/logs/
.dispatch/runs/<run-id>/heartbeats/
```

Status readers use these files to report agent counts by role and status,
active assignments, heartbeat freshness, pending decisions, and
`protocol.violation` events. Lifecycle events include `agent.spawned`,
`agent.heartbeat`, `workstream.assigned`, `agent.completed`, and
`agent.failed`.

## Worker Input

A worker receives:

- target repository path
- objective
- one imported workstream
- relevant repository instructions summarized in the explicit plan
- allowed file scope from the explicit plan
- dependency and parallel group context
- validation expectations

## Worker Output

A worker returns:

- status: `done`, `done_with_concerns`, `needs_context`, `blocked`, or `failed`
- summary
- changed files
- validation run
- questions or blockers

## Reviewer Input

A reviewer receives:

- target repository path
- objective
- imported workstream
- worker report
- changed-file summary
- validation evidence available so far
- acceptance criteria from the plan

## Reviewer Output

A reviewer returns:

- status: `accepted`, `changes_requested`, `blocked`, or `failed`
- findings or residual risks
- validation gaps
- recommendation for scheduler continuation

## Rule

Each worker owns one workstream at a time. Parallel workers must be told they are not alone in the codebase and must avoid files outside their declared scope.

Reviewer acceptance is a separate phase before a workstream is considered complete. A worker report alone is not completion evidence.

A coordinator report alone is also not implementation evidence. Any project-file
change must be attributable to a registered worker, reviewer, or validator with
an assigned scope and durable report.
