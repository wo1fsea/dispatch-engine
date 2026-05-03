---
language: en-US
audience: agent
doc_type: normative
---

# Issue Reporting Protocol

Use this protocol whenever interactive Codex, a Dispatch Engine coordinator, or
an operator using `de` finds a Dispatch Engine framework problem.

## Project Repository

- GitHub repo: `https://github.com/wo1fsea/dispatch-engine`
- Issue tracker: `https://github.com/wo1fsea/dispatch-engine/issues`

## What Must Be Reported

Open or prepare a GitHub issue when any of these happen while using this skill
or the bundled `de` runtime:

- The skill guidance is unclear, contradictory, stale, or causes unsafe
  workflow behavior.
- A Dispatch Engine runtime command fails because of Dispatch Engine behavior,
  state shape, CLI contract, provider command rendering, status reporting,
  prompt rendering, or `.dispatch/` protocol design.
- A workflow reaches a process blocker caused by the framework rather than by
  the target repository's product or code.
- A coordinator, worker, reviewer, validator, or heartbeat cannot follow the
  documented protocol because the protocol is incomplete or impossible.
- Status, alerts, events, decision records, heartbeats, reports, reviews, or
  validation evidence are missing, misleading, malformed, or too weak for
  interactive Codex to supervise the run.
- A dogfood run exposes friction that should change Dispatch Engine, the skill,
  references, prompt templates, or runtime.

Do not file Dispatch Engine issues for ordinary target-repository bugs,
expected product decisions, missing target-repo dependencies, or user-scoped
implementation defects unless they expose a Dispatch Engine framework problem.

## Reporting Behavior

Interactive Codex should report proactively:

1. Collect enough context to make the issue actionable.
2. Avoid secrets, credentials, private user content, and long logs.
3. If authenticated GitHub tooling is available, create the issue directly.
4. If GitHub tooling is unavailable, write a ready-to-file issue draft in the
   conversation and clearly state that creation was blocked by tooling or
   authentication.
5. Continue or pause the target run according to severity. Do not let issue
   filing silently replace user-facing status reporting.

Coordinators should not leave issue-worthy framework failures buried only in
provider chat. They should record a blocker or protocol violation under the
target repo's `.dispatch/` state when the active run is affected, and include a
GitHub issue draft in their coordinator report if they cannot create the issue.

## Required Issue Content

Use a concise title such as:

```text
[runtime] status --json omits autonomous decision context
[skill] heartbeat guidance conflicts with decision blocker protocol
[protocol] worker report contract cannot represent skipped validation
[dogfood] alpha-kitchen run exposes provider preflight gap
```

Issue body should include:

- **Context**: target repo, run id, Dispatch Engine commit/version, skill path,
  provider/profile, and host when relevant.
- **Problem**: what blocked or misled the workflow.
- **Expected behavior**: what Dispatch Engine should have made possible.
- **Evidence**: short command output, status/alert/event snippets, relevant
  `.dispatch/` paths, stderr summary, or links to logs. Keep excerpts minimal.
- **Impact**: whether the run is blocked, degraded, or only confusing.
- **Possible fix direction**: skill/reference/prompt/runtime, when obvious.
- **Privacy check**: confirm that no secrets or private target-repo content are
  included.

Preferred command when `gh` is available:

```bash
gh issue create \
  --repo wo1fsea/dispatch-engine \
  --title "<title>" \
  --body-file <issue-body.md>
```

If the issue was created, include the issue URL in the run report or user
update. If only a draft was prepared, include the draft and why it was not filed.
