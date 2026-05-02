---
language: en-US
audience: agent
doc_type: runbook
---

# Heartbeat Observation

Use this runbook when interactive Codex starts a detached Dispatch Engine run
and needs a truthful way to keep the foreground conversation updated.

## Boundary

The `de` CLI is a Codex-facing machine interface, not a human control panel.
Human operators talk to interactive Codex. Codex calls `de`, reads JSON and
`.dispatch/` state, interprets the result, and decides what to say next.

Detached execution keeps the foreground chat responsive, but it does not
automatically wake that chat. Dispatch Engine writes durable state; a user
message or a host-provided thread heartbeat must wake Codex before Codex can
read and explain that state.

Dispatch Engine itself does not send chat messages, schedule host wakeups, or
own the heartbeat. Keep heartbeat configuration in the Codex host layer.

## When To Use A Heartbeat

Create or suggest a host thread heartbeat after `de run <repo> --detach` when:

- the run is expected to last more than a few minutes
- workers, reviewers, or validators may finish while the user is away
- pending decisions, protocol violations, or failed agents need timely user
  attention
- the user asked for proactive progress updates
- the run has expensive or high-risk work where stale status would be costly

Do not create a heartbeat for quick checks where Codex can simply run
`status --json` before answering the next user message.

## Interval Guidance

Use the quietest interval that still protects the user:

- **5 minutes**: high-risk work, active decision points, failing agents, or
  time-sensitive validation.
- **10-15 minutes**: normal multi-agent implementation and review.
- **30 minutes**: long-running validation, slow research, or low-urgency
  background work.

Stop or let the heartbeat expire after the run completes, fails unrecoverably,
or no longer needs proactive observation.

## Heartbeat Prompt

The heartbeat prompt should describe the check to perform. Schedule, recurrence,
and thread identity belong in the host automation configuration, not in the
prompt text.

Template:

```text
Check the detached Dispatch Engine run for <target repo path>.

Use the Dispatch Engine skill at <dispatch-engine skill path>. Read the latest
run state with status --json, events --since <last-seen-event-id> --json, and
alerts --json. Report only material changes: completed workstreams, blocked
workstreams, failed agents, pending decisions, new protocol violations, run
completion, or validation evidence.

If a pending decision needs user approval, summarize the options and ask the
user before running resolve-decision. Do not resolve decisions on your own. Do
not claim progress from chat memory alone.
```

If the host supports per-run context, include the run id and last seen event id.
If not, Codex should derive the latest run from `status --json` and read alerts
as a snapshot.

## What To Report

Report only material changes:

- run completed, failed, or became blocked
- workstream completed, failed, or needs reassignment
- agent failed, stopped heartbeating, or produced malformed evidence
- new pending decision requires user approval
- new protocol violation needs repair
- new validation evidence changes confidence in completion

Skip unchanged activity. A heartbeat that finds no material change should stay
quiet unless the host requires a visible update.

## Control Surfaces

Use the Codex-facing CLI surfaces in this order:

1. `status --json`: primary summary, run state, agents, workstreams, pending
   decisions, protocol violations, and current next actions.
2. `events --since <event-id> --json`: delta reader for material changes since
   the last heartbeat.
3. `alerts --json`: snapshot of decisions, failures, violations, and other
   user-relevant risks.
4. `resolve-decision --id <decision-id> --option <option-id> --json`: write
   surface, only after explicit user approval.

## Fallback Wording

When host wakeups are unavailable, say:

```text
This detached Dispatch Engine run will keep writing queryable state under
.dispatch/, but this Codex chat will not wake itself automatically. I can check
the latest status whenever you send a message asking for progress.
```

When wakeups exist but the user has not approved one, say:

```text
I can leave the detached run queryable under .dispatch/ and check it on your
next message, or I can set up a host heartbeat so this thread periodically wakes
and I summarize only material changes.
```
