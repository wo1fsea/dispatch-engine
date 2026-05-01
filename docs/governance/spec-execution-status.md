---
language: en-US
audience: agent
doc_type: normative
---

# Spec Execution Status

## Principle

Status is code. Status changes must be explicit file changes, reviewable in diffs, and tied to evidence.

Never encode status in directory names. Keep `specs/<spec-id>/` stable so links from commits, PRs, and notes do not break.

## Required Structure

```text
specs/<spec-id>/
  PRODUCT.md
  TECH.md
  STATUS.md
  workstreams/
    01-implementation.md
```

`STATUS.md` is the global board. It records the overall lifecycle, implementation progress, validation progress, and a summary table of workstreams.

`workstreams/*.md` files are the concurrency unit. Agents should primarily update their own workstream file and synchronize only their row in `STATUS.md`.

Use `docs/governance/multi-agent-spec-flow.md` when multiple agents or branches implement the same spec in parallel.

## Overall Spec Status

Use these values for the frontmatter `status` field in `STATUS.md`:

- `draft`: product or technical direction is still being shaped; implementation should not start.
- `ready`: spec is accepted enough to begin; implementation has not started.
- `active`: at least one workstream is claimed or in progress.
- `blocked`: work is stopped on an external decision, dependency, or failing prerequisite.
- `ready-review`: implementation and validation are complete enough for review, but not merged.
- `done`: implementation is merged or shipped, validation is complete, and specs match reality.
- `superseded`: replaced by another spec or decision.
- `cancelled`: explicitly abandoned.

Use these values for progress fields:

- `not_started`
- `partial`
- `complete`

Common combinations:

- Not started: `status: ready`, `implementation: not_started`, `validation: not_started`.
- Partially complete: `status: active`, `implementation: partial`, `validation: partial`.
- Complete: `status: done`, `implementation: complete`, `validation: complete`.

## Workstream Status

Use this state machine for each `workstreams/*.md` file:

```text
ready -> claimed -> in_progress -> implemented -> validating -> validated -> merged
           |             |              |
           v             v              v
        released      blocked        blocked
```

Rules:

- `implemented` means code is written but validation is not complete.
- `validated` means validation evidence exists but the work may not be merged.
- `merged` means the workstream has landed in the target branch.
- `released` means the claim was intentionally given up and the work can return to `ready`.
- Do not use `done` for workstreams; it is too ambiguous.
- Do not jump from `ready` to `merged`.

## Claiming Work

Before starting implementation, an agent must claim a workstream by updating its frontmatter with status, owner, branch when known, and updated date.

For parallel work, include `claimed_at` and `lease_expires_at`.

Do not take over another owner’s workstream unless the previous owner released it, the coordinator reassigned it, or the workstream is clearly stale by project policy.

## Evidence

Every status transition must add an Activity Log entry.

For `blocked`, include:

```markdown
## Blocked

Reason:
Unblock when:
Owner to unblock:
```

## STATUS.md Sync Rules

When updating a workstream:

1. Update the workstream file first.
2. Update only that workstream’s row in `STATUS.md`.
3. Update `STATUS.md` summary fields only when the aggregate status changed.
4. Do not rewrite unrelated rows or reformat the whole table.

## Completion Criteria

A spec can be marked `done` only when:

- Required implementation workstreams are `merged`.
- Validation is complete and recorded.
- `PRODUCT.md` describes the behavior that shipped.
- `TECH.md` describes the implementation shape that landed.
- Follow-ups are either complete, moved to a new spec/issue, or explicitly deferred.
