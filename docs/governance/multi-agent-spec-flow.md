---
language: en-US
audience: agent
doc_type: normative
---

# Multi-Agent Spec Flow

Use this workflow when multiple agents, branches, or owners may implement the same spec in parallel.

## Model

```text
Spec = product and technical intent plus overall status
Workstream = concurrency unit owned by one agent or owner at a time
Agent = claims and updates one workstream
Integrator = coordinates conflicts, merge order, and final validation
```

## Workstream Status Machine

```text
ready -> claimed -> in_progress -> implemented -> validating -> validated -> merged
           |             |              |
           v             v              v
        released      blocked        blocked
```

Do not use `done` for workstreams.

## Claim And Lease

Each workstream frontmatter should include:

```yaml
id: 01-contract
status: claimed
owner: agent-a
branch: codex/gh-123/01-contract
pr:
files:
  - src/api/*
depends_on: []
claimed_at: 2026-04-30T10:00:00+08:00
lease_expires_at: 2026-04-30T12:00:00+08:00
updated: 2026-04-30
```

Rules:

- Claim before editing.
- Use a lease so stale claims can be recovered.
- Update `lease_expires_at` when continuing substantial work.
- Do not take over another owner’s active lease without coordinator action or clear stale-policy evidence.
- When releasing work, set status to `released`, record why, then coordinator or next owner can move it to `ready`.

## Agent Update Rules

- Update your workstream file first.
- Update only your row in `STATUS.md`.
- Do not rewrite the entire `STATUS.md` table.
- Do not edit another agent’s workstream except for coordinator-approved handoff or mechanical conflict resolution.
- Add an Activity Log entry for every status transition.

## Dependency And Conflict Rules

- Use `depends_on` for ordered work.
- Shared contracts should usually be their own workstream, such as `01-contract.md`.
- If two agents need the same files, split the workstream or appoint an integrator.
- Contract changes must update `TECH.md` before dependent workstreams rely on them.

## Integrator Flow

```text
draft/ready spec
-> coordinator splits workstreams
-> agents claim with leases
-> agents implement and validate
-> workstreams reach validated
-> integrator checks conflicts and merge order
-> workstreams merge
-> full validation runs
-> STATUS.md moves to ready-review
-> review/merge
-> STATUS.md moves to done
```

The overall spec can be `done` only when required workstreams are `merged`, validation is complete, specs match reality, and follow-ups are tracked or explicitly deferred.
