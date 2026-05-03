---
language: en-US
audience: agent
doc_type: normative
---

# Operator Flow

Use this reference when interactive Codex is supervising Dispatch Engine.

For install, copy/clone setup, target repo quickstart commands, status/tail
usage, `.dispatch/` git guidance, and troubleshooting, see
`references/operator-guide.md`.
For heartbeat wakeup prompts, interval guidance, material-change reporting, and
fallback wording, see `references/heartbeat-observation.md`.
For framework, skill, runtime, protocol, prompt, status, heartbeat, or process
blocker reporting, see `references/issue-reporting-protocol.md`.

## Boundary

Interactive Codex plus the skill owns repository discovery, planning judgment, workstream splitting, review, validation strategy, and user conversation. Dispatch Engine runtime owns explicit plan import, durable `.dispatch/` state, status/tail, event logs, foreground or detached coordinator launch, and mechanical helpers only where durable/queryable state is required.

Dispatch Engine-generated non-project runtime content must live under `.dispatch/` in the target repository. Accepted project work stays in the target repository's normal project paths.

The bundled `de` CLI is Codex-facing. Human operators should normally talk to
interactive Codex, while Codex calls `de`, reads JSON/file state, and explains
progress or asks for decisions.

## Flow

1. Read the target repository's local instructions, governance, source layout, tests, docs, and the user's objective from interactive Codex.
2. Summarize the planning basis: relevant repo rules, workstream boundaries, dependencies, write scopes, validation strategy, risks, and unresolved decisions.
3. Create an explicit dispatch plan from that Codex-owned context.
4. Store any Dispatch Engine-generated plan file under `.dispatch/plans/`.
5. Import the explicit plan into `.dispatch/runs/<run-id>/` with `python3 scripts/de.py init <repo> --plan <repo>/.dispatch/plans/<plan-id>.json`.
6. Ask the user before high-risk execution, parallel work, or unresolved decisions.
7. Preview coordinator launch with `python3 scripts/de.py run <repo> --dry-run`; omitting `--provider` uses the default `codex` provider, while `--provider claude` is optional.
8. Prefer `python3 scripts/de.py run <repo> --detach` from interactive Codex so the conversation can continue while status and tail are polled.
9. Immediately after every successful interactive detached launch, create a host-layer thread heartbeat for the current thread. This is required when the host supports wakeups, and the default interval is 15 minutes.
10. Configure the heartbeat to read Dispatch Engine JSON state, summarize material changes, request user input only for decisions or unrecoverable blockers, apply the four-heartbeat autonomous technical-decision fallback when allowed by interactive Codex eligibility judgment, and stop itself when `status --json` reports `completed`, `failed`, or `cancelled`.
11. If the host cannot create a heartbeat, tell the user the detached run will not be proactively supervised and ask before continuing.
12. Monitor status and event logs through `status --json`, `events --since`, `alerts --json`, `tail`, and `.dispatch/runs/` files.
13. If the user asks to stop a run, call
    `python3 scripts/de.py cancel <repo> --run-id <run-id> --reason "<reason>" --json`.
    The `stop` command is an alias for natural-language use, while `cancel`
    remains canonical. Cancellation is terminal but distinct from failure,
    preserves `.dispatch/` evidence, and should be followed by `status --json`,
    `events --since`, and `alerts --json` before reporting the reason once and
    stopping the heartbeat.
14. Resolve decisions explicitly after user approval, using `resolve-decision`.
    Technical decisions may be resolved autonomously only after four
    consecutive unanswered heartbeat checks. Use `resolve-decision
    --autonomous-technical --unanswered-heartbeats <count>
    --autonomous-rationale <text> --validation-expected <command> --json`; the
    runtime defaults actor to `interactive-codex-autonomous`, writes the
    source-of-truth record to `decisions.jsonl`, validates only metadata
    invariants, and exposes a convenience `status --json`
    `autonomous_decisions` summary.
15. Report validation evidence, residual risk, and all autonomous technical choices made during the run.
16. If Dispatch Engine itself creates a framework problem or process blocker,
    proactively file or prepare a GitHub issue against
    `https://github.com/wo1fsea/dispatch-engine/issues` using
    `references/issue-reporting-protocol.md`.

## Runtime Loop

The loop is imported plan -> DE launches provider coordinator -> coordinator spawns workers/reviewers/validators through provider-native mechanisms -> agents write role-specific evidence -> DE status/tail reads `.dispatch/` state. User interaction remains outside the runtime in interactive Codex, which can keep talking with the user while polling status and tail output.

Detached execution is not the same as proactive foreground awareness. Dispatch
Engine can keep writing state in the background, but interactive Codex only
interprets that state after a user message or a host wakeup such as a thread
heartbeat automation. For interactive detached runs, that heartbeat is a
required supervision companion and must be stopped when the run reaches a
terminal state. A cancelled run should be reported once with its cancellation
reason from `status --json` before the heartbeat is stopped.

If host wakeups are unavailable, use this wording:

```text
This host cannot create the required Dispatch Engine heartbeat for this thread.
The detached run would still write queryable state under .dispatch/, but this
chat would not be proactively supervised. Please confirm whether to continue
without proactive observation or switch to a foreground/debug run.
```

See `references/orchestrator-loop.md` for the adapter-neutral design.

## Guardrail

Interactive Codex operates Dispatch Engine through CLI commands and files. It should not rely on private chat runtime internals as durable orchestration state, and the runtime should not infer repository conventions from broad scans when an explicit plan is required.
