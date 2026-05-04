---
language: en-US
audience: agent
doc_type: normative
---

# Issue Triage Governance

Use this workflow when reviewing, updating, closing, or implementing Dispatch
Engine GitHub issues, especially dogfood issues created from local `.dispatch/`
run state.

Use `references/issue-reporting-protocol.md` for when and how to create new
Dispatch Engine issues. Use this document after issues exist.

## Triage Rule

Do not implement, close, or rewrite an issue from its title alone. Verify the
issue against the current repository commit, current skill installation when
relevant, and the cited local run state or command output.

## Evidence To Check

For each issue, collect the smallest useful evidence:

- Issue title, body, comments, labels, and creation time.
- Current Dispatch Engine commit and installed skill commit when relevant.
- The cited target repo, run id, and `.dispatch/runs/<run-id>/` files.
- `de status --json` and `de alerts --json` for the cited run when available.
- Relevant `agents/`, `workstreams/`, `reports/`, `reviews/`, `validation/`,
  `events.jsonl`, `decisions.jsonl`, `supervisors/`, and heartbeat files.
- Current runtime or prompt code when the issue claims a framework defect.

Prefer short excerpts over long logs. Keep private target-repo content out of
GitHub comments unless the user explicitly approves it.

## Classify Before Acting

Assign one of these outcomes before implementation:

- **Current defect**: still reproduces on current code or the current design
  still lacks the required invariant.
- **Historical defect, now clean**: the cited run or invariant is now clean
  because a later repair or code change fixed it.
- **Partially stale**: part of the issue still holds, but the title/body now
  points at outdated evidence or the wrong root cause.
- **Duplicate**: the remaining defect is already tracked by another open issue
  or spec.
- **Target-repo issue**: the failure is ordinary target project behavior, not a
  Dispatch Engine framework, skill, protocol, prompt, heartbeat, status, or
  process problem.

## Action Rules

- For a current defect, create or update a spec before implementation when the
  fix changes runtime behavior, protocol shape, prompt guidance, status/alert
  semantics, or cross-file governance. Compact specs are enough for narrow
  bug fixes.
- For a historical defect that is now clean, comment with the commit or local
  state evidence and close the issue unless it still describes a missing
  invariant.
- For a partially stale issue, add a correction comment or edit the issue body
  when appropriate, then keep only the current invariant open.
- For a duplicate, cross-link the canonical issue and close the duplicate.
- For a target-repo issue, explain why it is outside Dispatch Engine scope and
  close or move it to the target project tracker.

Do not close an issue only because one run reached a terminal state. A terminal
run can still expose a missing protocol invariant. Conversely, do not keep an
issue open only because old evidence exists when current status, alerts, and
tests prove the invariant is now clean.

## Dogfood-Specific Checks

When a dogfood issue cites local run state:

1. Check whether the issue describes current status output, historical
   operator confusion, or a missing future invariant.
2. Distinguish detected protocol violations from `protocol.violation` events;
   event payloads may be stale, malformed, or from a previous coordinator
   behavior.
3. Compare `run.json` workstreams with `workstreams/*.json`; stale aggregate
   state and per-workstream state should be called out separately.
4. For provider-native worker issues, check both canonical runtime fields and
   nested launch evidence such as provider spawn references, heartbeat paths,
   and missing reports.
5. If a repair worker later made the run clean, classify the original issue as
   either historical-fixed or as a process invariant about preventing the
   dirty intermediate state.

## Closure Evidence

When closing an issue, leave a concise comment with:

- The commit or local state checked.
- The command or file evidence.
- Whether the issue was fixed, superseded, duplicated, or out of scope.
- Any follow-up issue or spec that keeps the remaining invariant alive.
