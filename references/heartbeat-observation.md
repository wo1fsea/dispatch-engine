---
language: en-US
audience: agent
doc_type: runbook
---

# Heartbeat Observation

Use this runbook whenever interactive Codex starts a detached Dispatch Engine
run. Heartbeat observation is required for interactive detached runs when the
Codex host supports thread wakeups.

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

The dashboard observer is also outside the heartbeat. For active Dispatch
Engine sessions, interactive Codex should launch or reuse it with
`python3 scripts/de.py dashboard <repo> --detach --json` and open the returned
`url` in the Codex in-app browser when available. The dashboard is read-only
visibility for humans and Codex; it does not create wakeups, perform
supervision, mutate `.dispatch/` state, or replace heartbeat checks.
The dashboard URL is current only for the run id selected by the dashboard
command. If a continuation run supersedes an older run, the heartbeat check
still reads `status --json`, `events --since`, and `alerts --json` for the new
run, while Codex launches or reports the new dashboard URL and labels the old
URL stale/superseded. If a run reaches terminal state, any still-open dashboard
is historical inspection rather than evidence that the run remains active.

## Required Lifecycle

After every successful interactive `de run <repo> --detach` launch:

1. Create a host thread heartbeat for the current Codex thread.
2. Store enough prompt context for the heartbeat to identify the target repo,
   Dispatch Engine skill path, run id when known, and last seen event cursor.
3. On each wakeup, read `status --json`, `events --since`, and `alerts --json`.
4. Record the host heartbeat snapshot for the run with
   `record-host-heartbeat`, including the host `automation_id`, owner,
   interval, last wakeup, next wakeup when known, and last observed event
   cursor.
5. Report only material changes.
6. If the run reaches `completed`, `failed`, or `cancelled`, report the terminal
   state once, include the cancellation reason when available, write a stopped
   host heartbeat snapshot with `--status stopped`, `--stopped-at`, and
   `--stop-reason`, then pause, delete, or otherwise stop the heartbeat.
7. Before stopping a heartbeat for a terminal run, check `status --json`
   `lifecycle_diagnostics` and `alerts --json`. Orphaned running agents, stale
   detached supervisors, provider-native active agents without role-specific
   reports, stdout-only decision requests, and coordinator reports that list
   `decisions_required` without durable decision evidence are material even
   when terminal `next_actions` is empty.
8. If the terminal run has a dashboard observer, describe it as terminal
   historical inspection rather than live progress. For continuation runs,
   launch or report the dashboard URL for the new run and call older observer
   URLs stale/superseded unless the user asks to inspect the old run.
9. Track pending technical decisions across heartbeat wakeups. If the same
   technical decision is still unresolved after four consecutive heartbeat
   checks, apply the autonomous technical-decision rule below.

This is a lifecycle requirement, not an optional recommendation. Do not treat a
detached run as proactively supervised until the heartbeat exists. If the host
cannot create a heartbeat, tell the user before continuing the detached run
workflow.

The snapshot producer boundary is the outer interactive Codex host heartbeat.
Coordinators may read and summarize host heartbeat state, but they must not
synthesize wakeup timestamps or write real run-scoped snapshots. The reserved
coordinator-style id family `codex-thread-heartbeat-*` is rejected by
`record-host-heartbeat` because it is not evidence of the host automation that
wakes the foreground chat.

Opening the dashboard URL is useful operator visibility, but it does not make a
detached run proactively supervised. Keep the heartbeat active until the run
reaches a terminal state or the user explicitly abandons the run.

## Interval Guidance

Default heartbeat interval is **15 minutes**. In the Codex App heartbeat
automation, use:

```text
FREQ=MINUTELY;INTERVAL=15
```

Override the default only when the run risk or urgency clearly justifies it:

- **5 minutes**: high-risk work, active decision points, failing agents, or
  time-sensitive validation.
- **15 minutes**: default for normal multi-agent implementation, review, and
  validation.
- **30 minutes**: long-running validation, slow research, or low-urgency
  background work.

Stop the heartbeat after the run completes, fails unrecoverably, is cancelled,
or is explicitly abandoned by the user. Do not leave stale heartbeat monitors
polling finished Dispatch Engine runs.

## Snapshot Recording

After every heartbeat check, write `.dispatch/runs/<run-id>/host-heartbeat.json`
through the Codex-facing helper from the outer interactive Codex host heartbeat:

```bash
python3 scripts/de.py record-host-heartbeat <repo> \
  --run-id <run-id> \
  --automation-id <host-automation-id> \
  --owner interactive-codex \
  --status active \
  --interval-seconds 900 \
  --last-wakeup-at <iso-timestamp> \
  --last-observed-cursor <event-id> \
  --json
```

Pass `--next-wakeup-at` when the host provides it. If omitted, the helper
derives it from `--last-wakeup-at` and `--interval-seconds`.
Do not pass coordinator-synthesized automation ids such as
`codex-thread-heartbeat-<run-id>`; those are rejected and must not be used to
reset dashboard freshness.

Before deleting or pausing the host automation for a terminal run, record the
stopped snapshot:

```bash
python3 scripts/de.py record-host-heartbeat <repo> \
  --run-id <run-id> \
  --automation-id <host-automation-id> \
  --owner interactive-codex \
  --status stopped \
  --interval-seconds 900 \
  --last-wakeup-at <iso-timestamp> \
  --last-observed-cursor <event-id> \
  --stopped-at <iso-timestamp> \
  --stop-reason "terminal run reached" \
  --json
```

The dashboard reads this run-scoped snapshot through `/api/host-heartbeat`.
When the snapshot is missing for an active run, dashboard state stays missing
rather than inferring freshness from agent heartbeats.

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
completion, protocol-violation resolution records, or validation evidence.

After each check, run record-host-heartbeat from the outer host heartbeat for this run with the host
automation id, owner, interval, last wakeup timestamp, next wakeup timestamp
when known, and last observed event cursor. If a pending decision needs user
approval, summarize the options and ask the user before running
resolve-decision. Do not resolve decisions on your own unless the
four-heartbeat autonomous technical-decision fallback applies. Do not claim
progress from chat memory alone. If status --json shows the run is completed,
failed, or cancelled, report that terminal state, write record-host-heartbeat
with --status stopped before deleting or pausing the host automation, and stop
this heartbeat. For cancelled runs, include status --json cancellation.reason
and any run.cancel events from events --since.

If the same pending technical decision has been reported across four
consecutive heartbeat checks without user resolution, use interactive Codex
judgment to confirm that the decision is eligible, choose the conservative
technical option, run resolve-decision with --autonomous-technical, and
continue the run. Record rationale and expected validation so the source
record in decisions.jsonl and the status --json autonomous_decisions summary
can support the final report.
```

If the host supports per-run context, include the run id and last seen event id.
If not, Codex should derive the latest run from `status --json` and read alerts
as a snapshot.

## What To Report

Report only material changes:

- run completed, failed, became blocked, or was cancelled
- workstream completed, failed, or needs reassignment
- agent failed, stopped heartbeating, or produced malformed evidence
- new pending decision requires user approval, or qualifies for the
  four-heartbeat autonomous technical-decision fallback
- stdout appears to request a user decision but no pending decision record or
  `decision.requested` event exists
- a coordinator report lists `decisions_required` but no pending decision
  record or `decision.requested` event exists
- a worker, reviewer, or validator is running without launch evidence
- a provider-native spawned worker, reviewer, or validator remains active
  without a role-specific report after the staleness window
- a detached supervisor is stale, or a terminal coordinator/run has orphaned
  still-running worker, reviewer, or validator agents
- new unresolved protocol violation needs repair
- new protocol-violation resolution changes the audit state
- new validation evidence changes confidence in completion

Skip unchanged activity. A heartbeat that finds no material change should stay
quiet unless the host requires a visible update.

## Autonomous Technical Decisions

After four consecutive heartbeat checks where the same pending technical
decision remains unresolved by the user, outer interactive Codex plus the
heartbeat owns the eligibility judgment and may resolve that decision without
waiting longer, but only when all of these are true:

- the decision is technical rather than product, legal, financial, security,
  privacy, deployment, credential, or irreversible data behavior
- the choice stays inside the already approved user objective
- the selected option is conservative, reversible, and minimizes new scope
- the selected option does not discard or overwrite user or worker changes
- the selected option can be validated by normal project checks

Do not autonomously resolve decisions that change product behavior, authorize
deployment, handle secrets, delete data, broaden business scope, or create
nontrivial user-facing commitments. Keep those pending and keep asking.

When autonomous resolution is allowed, use the Codex-facing decision surface:

```bash
python3 scripts/de.py resolve-decision <repo> \
  --id <decision-id> \
  --option <option-id> \
  --autonomous-technical \
  --unanswered-heartbeats 4 \
  --heartbeat-interval-minutes 15 \
  --first-seen-heartbeat-id <heartbeat-id> \
  --last-seen-heartbeat-id <heartbeat-id> \
  --autonomous-rationale "<why this option is conservative/reversible>" \
  --validation-expected "<validation command>" \
  --json
```

With `--autonomous-technical`, the runtime defaults the actor to
`interactive-codex-autonomous`. Explicit actor overrides must match that value.
The runtime only validates mechanical metadata: the unanswered heartbeat count,
required rationale, standard excluded categories, conservative/reversible
assertions, and validation expectation shape. It does not infer whether the
choice is truly technical or pick the option.

The source of truth is the append-only record in
`.dispatch/runs/<run-id>/decisions.jsonl`. `status --json` may expose an
`autonomous_decisions` count and compact records as a convenience for heartbeat
and final-report summarization; do not treat the summary as the durable record.
Do not apply the autonomous technical fallback to stdout-only questions or
coordinator report `decisions_required` entries unless a matching pending
decision record exists.

The heartbeat should keep an in-thread list of autonomous choices made during
the run. The final completion report must include every autonomous decision
with:

- decision id
- selected option
- why it qualified as technical
- why the selected option was conservative
- validation evidence after the choice

## Control Surfaces

Use the Codex-facing CLI surfaces in this order:

1. `status --json`: primary summary, run state, agents, workstreams, pending
   decisions, protocol violations, autonomous decision summaries, and current
   next actions. Its `lifecycle_diagnostics` entries surface stdout-only and
   report-only decision requests as material diagnostics when durable decision
   evidence is missing.
2. `events --since <event-id> --json`: delta reader for material changes since
   the last heartbeat.
3. `alerts --json`: snapshot of decisions, failures, violations, and other
   user-relevant risks.
4. `record-host-heartbeat --run-id <run-id> --automation-id <id> --owner
   interactive-codex --status <active|stopped> --interval-seconds <seconds>
   --last-wakeup-at <timestamp> --last-observed-cursor <event-id> --json`:
   run-scoped snapshot writer for `.dispatch/runs/<run-id>/host-heartbeat.json`.
   Use only from the outer interactive Codex host heartbeat with the real host
   automation id.
5. `cancel --run-id <run-id> --reason <text> --json`: user-requested
   cancellation control. Use `stop` only as a natural-language alias. After it
   returns, read `status --json`, `events --since`, and `alerts --json`, report
   the terminal cancelled state once, and stop the heartbeat.
6. `resolve-decision --id <decision-id> --option <option-id> --json`: write
   surface after explicit user approval.
7. `resolve-decision --autonomous-technical --unanswered-heartbeats <count>
   --autonomous-rationale <text> --validation-expected <command> --json`:
   structured write surface for an allowed four-heartbeat autonomous technical
   fallback.
8. `resolve-protocol-violation --violation <name> --resolution <kind>
   --rationale <text> --evidence <text> --json`: append a protocol-violation
   audit resolution after review. Add `--agent-id` and `--workstream` when the
   selector would otherwise be ambiguous. Supported kinds are `acknowledged`,
   `accepted_with_concerns`, `superseded_by_validation`, and `false_positive`.

Protocol-violation resolution is an audit overlay only. It preserves the
original violation evidence, does not rewrite a completed/failed/cancelled run,
and does not relax capability-profile rules for future workers. Heartbeats
should treat `status --json` unresolved counts as the repair queue and
`protocol_violation_resolutions` as the audit trail.

## Fallback Wording

When host wakeups are unavailable, say:

```text
This host cannot create the required Dispatch Engine heartbeat for this thread.
The detached run would still write queryable state under .dispatch/, but this
chat would not be proactively supervised. Please confirm whether to continue
without proactive observation or switch to a foreground/debug run.
```
