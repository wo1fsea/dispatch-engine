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
9. For long-running detached work, create or suggest a host-layer thread heartbeat when the current Codex host supports wakeups. The heartbeat should wake the current thread and ask Codex to read Dispatch Engine JSON state, summarize material changes, and request user input only for decisions or unrecoverable blockers.
10. If no heartbeat is configured or supported, tell the user that Codex will read the latest `.dispatch/` state when they next ask for progress.
11. Monitor status and event logs through `status --json`, `events --since`, `alerts --json`, `tail`, and `.dispatch/runs/` files.
12. Resolve decisions explicitly after user approval, using `resolve-decision`.
13. Report validation evidence and residual risk.

## Runtime Loop

The loop is imported plan -> DE launches provider coordinator -> coordinator spawns workers/reviewers/validators through provider-native mechanisms -> agents write role-specific evidence -> DE status/tail reads `.dispatch/` state. User interaction remains outside the runtime in interactive Codex, which can keep talking with the user while polling status and tail output.

Detached execution is not the same as proactive foreground awareness. Dispatch
Engine can keep writing state in the background, but interactive Codex only
interprets that state after a user message or a host wakeup such as a thread
heartbeat automation.

If host wakeups are unavailable, use this wording:

```text
This detached Dispatch Engine run will keep writing queryable state under
.dispatch/, but this Codex chat will not wake itself automatically. I can check
the latest status whenever you send a message asking for progress.
```

See `references/orchestrator-loop.md` for the adapter-neutral design.

## Guardrail

Interactive Codex operates Dispatch Engine through CLI commands and files. It should not rely on private chat runtime internals as durable orchestration state, and the runtime should not infer repository conventions from broad scans when an explicit plan is required.
