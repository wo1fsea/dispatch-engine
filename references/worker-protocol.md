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
