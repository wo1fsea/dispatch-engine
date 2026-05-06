---
language: en-US
audience: mixed
doc_type: runbook
---

# Operator Guide

Use this guide when installing Dispatch Engine as a Codex skill and operating it against a target repository.

Project repository: `https://github.com/wo1fsea/dispatch-engine`.
Framework, skill, runtime, protocol, heartbeat, prompt, status, or process
blocker issues belong in `https://github.com/wo1fsea/dispatch-engine/issues`.
Use `references/issue-reporting-protocol.md` to file or draft actionable issues.

## Install Shape

Dispatch Engine is distributed as the skill directory itself. The repository root contains `SKILL.md`, reference guidance, prompt templates, and the bundled runtime under `scripts/`. There is no separate package installer for the current usable version.

Install by cloning or copying the whole repository root into a Codex skills directory, commonly `$CODEX_HOME/skills/dispatch-engine` or `~/.codex/skills/dispatch-engine` when `CODEX_HOME` is unset.

Clone install:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
git clone https://github.com/wo1fsea/dispatch-engine.git "$CODEX_HOME/skills/dispatch-engine"
cd "$CODEX_HOME/skills/dispatch-engine"
python3 scripts/de.py --help
python3 scripts/de.py version
```

Copy install from an existing checkout:

```bash
SOURCE=/path/to/dispatch-engine
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills/dispatch-engine"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.dispatch/' \
  "$SOURCE/" "$CODEX_HOME/skills/dispatch-engine/"
cd "$CODEX_HOME/skills/dispatch-engine"
python3 scripts/de.py --help
python3 scripts/de.py version
```

Keep the runtime in the skill repo. If `scripts/de.py` or `scripts/dispatch_engine/` is missing, the skill is not installable yet.

## Target Repo Quickstart

Set paths once:

```bash
DE_SKILL="${CODEX_HOME:-$HOME/.codex}/skills/dispatch-engine"
TARGET=/path/to/target-repo
```

Interactive Codex stays outside the runtime and remains the user-facing operator. It reads the target repo's local instructions, keeps talking with the user, prepares an explicit dispatch plan, asks for decisions, reviews results, and checks progress with `status` and `tail`.

Create a plan file under the target repo:

```bash
mkdir -p "$TARGET/.dispatch/plans"
$EDITOR "$TARGET/.dispatch/plans/plan-001.json"
```

Minimum plan shape:

```json
{
  "schema_version": 1,
  "plan_id": "plan-001",
  "objective": "Describe the user-visible objective.",
  "workstreams": [
    {
      "id": "01-docs",
      "title": "Update docs",
      "scope": "Concrete work assigned to this worker.",
      "files": ["README.md"],
      "depends_on": [],
      "validation": ["python3 scripts/de.py --help"]
    }
  ],
  "decisions": []
}
```

Import the plan:

```bash
python3 "$DE_SKILL/scripts/de.py" init "$TARGET" --plan "$TARGET/.dispatch/plans/plan-001.json"
python3 "$DE_SKILL/scripts/de.py" status "$TARGET"
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET"
```

Preview coordinator launch before starting a provider:

```bash
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --dry-run
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --provider codex --dry-run
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --provider claude --dry-run
```

Start a live foreground coordinator:

```bash
python3 "$DE_SKILL/scripts/de.py" run "$TARGET"
```

When operating from interactive Codex, prefer detached launch so the
conversation can continue while the coordinator runs:

```bash
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --detach
python3 "$DE_SKILL/scripts/de.py" status "$TARGET"
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET"
```

Omitting `--provider` defaults to provider `codex`, using a `codex exec --sandbox danger-full-access` command shape. `--provider codex` selects the same provider explicitly. `--provider claude` is optional and uses a Claude CLI command shape based on `claude --dangerously-skip-permissions --permission-mode bypassPermissions -p`.

For active Dispatch Engine sessions, also start or reuse the read-only
dashboard observer:

```bash
python3 "$DE_SKILL/scripts/de.py" dashboard "$TARGET" --detach --json
```

The JSON response includes a `url` when the service is running. Interactive
Codex should open that URL in the Codex in-app browser when the host provides
one. The dashboard is a local observer for run state and static UI assets; it
does not replace heartbeat supervision, `status --json`, `events --since`, or
`alerts --json`, and it must not be treated as a write surface.

Dashboard observer lifecycle is tied to the selected run id. By default
`dashboard --detach --json` selects the latest run; pass `--run-id <run-id>` to
inspect or revive a specific historical run. After a detached launch, report the
dashboard URL for the current run together with the host heartbeat status. When
`status --json` reports `completed`, `failed`, or `cancelled`, record a stopped
host heartbeat snapshot with `record-host-heartbeat --status stopped`, stop the
host heartbeat, and treat any still-open dashboard as terminal historical
inspection, not live progress. When a continuation run supersedes an older run,
launch or reuse the dashboard for the continuation run, report the new URL, and
label the old URL or old `dashboard --status --run-id <old-run-id> --json`
result stale/superseded unless the user explicitly wants historical inspection.

Recorded dashboard process metadata lives at
`.dispatch/runs/<run-id>/dashboard/server.json` and is also summarized by
`dashboard --status --run-id <run-id> --json`. Use that metadata before stopping
an observer; do not kill a dashboard process just because a newer run exists.
Stop only a recorded observer that belongs to the run being retired, or stop it
when the operator asked for cleanup.

Detached runs do not automatically wake the foreground Codex chat. After every
successful interactive `run --detach`, interactive Codex must create a
host-layer thread heartbeat when the current host supports wakeups. The
heartbeat wakes Codex, and Codex then reads Dispatch Engine state and reports
only material changes. After every heartbeat check, Codex must write
`.dispatch/runs/<run-id>/host-heartbeat.json` with `record-host-heartbeat` so
the dashboard can show host heartbeat freshness. When the run completes, fails,
or is cancelled, Codex must write a stopped snapshot before stopping the
heartbeat. Dispatch Engine does not send chat messages or own the host wakeup.
The default heartbeat interval is 15 minutes. If the same pending
technical decision remains unanswered across four consecutive heartbeat checks,
outer Codex plus the heartbeat owns the eligibility judgment and may select a
conservative, reversible option. Record it with `resolve-decision
--autonomous-technical`; the runtime defaults actor to
`interactive-codex-autonomous`, validates only the supplied metadata, appends
the source-of-truth record to `decisions.jsonl`, and exposes compact
`status --json` autonomous decision summaries. Final reporting must list all
such autonomous choices.

See `references/heartbeat-observation.md` for the required heartbeat lifecycle,
recommended intervals, the heartbeat prompt shape, material-change rules, and
fallback wording when wakeups are unavailable.

The host heartbeat snapshot is a real host automation record, not coordinator
progress evidence. Coordinators may read and summarize it, but they must not
synthesize wakeup timestamps or call `record-host-heartbeat` with a synthetic
automation id such as `codex-thread-heartbeat-<run-id>`; the CLI rejects that
reserved id family so coordinator flow cannot reset the visible countdown.

The provider process launched by `de run` is a coordinator only. It may plan, dispatch, monitor, summarize, request decisions, and write Dispatch Engine runtime state under `.dispatch/`, but it must not directly implement project-file changes. Project implementation belongs to registered workers, reviewers, or validators using provider-native spawn mechanisms, normalized capability profiles, and the shared `.dispatch/` observability contract.

### Provider Worker Launch

Registration is not launch evidence. A coordinator must not mark a
worker/reviewer/validator `running` or emit `agent.spawned` until it has
attempted a provider-native spawn or an explicit codex CLI fallback for that
agent. Durable evidence should include the prompt snapshot, provider spawn
reference or CLI command, stdout/stderr log paths for CLI fallback,
role-specific report path, and heartbeat evidence. If no launch path works, the
agent or workstream should be marked `failed` or `blocked` with the reason
instead of presenting fake running state.

For provider-native spawn, write `provider_native_agent_id` on the agent record
as the canonical launch evidence field. `status --json` also accepts legacy
dogfood fields `provider_native_spawn_ref`,
`launch_evidence.spawn_agent_id`,
`launch_evidence.provider_native_spawn_ref`, and
`provider_launch.evidence.provider_native_spawn_ref`. CLI fallback stdout and
stderr paths count as launch evidence only when the referenced log file exists.

Imported workstreams may include `validation_warnings` when validation commands
appear inconsistent with the normalized capability profile, such as service
startup under `service_start: deny` or local HTTP checks under
`network_access: none`. Treat those warnings as pre-dispatch prompts to narrow
validation, request a decision, or block the workstream.

## Watching Progress

Use these while the external interactive Codex remains in conversation with the user:

```bash
python3 "$DE_SKILL/scripts/de.py" status "$TARGET"
python3 "$DE_SKILL/scripts/de.py" status "$TARGET" --run-id <run-id>
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET"
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET" --run-id <run-id>
python3 "$DE_SKILL/scripts/de.py" status "$TARGET" --json
python3 "$DE_SKILL/scripts/de.py" events "$TARGET" --since <event-id> --json
python3 "$DE_SKILL/scripts/de.py" alerts "$TARGET" --json
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET" --json
python3 "$DE_SKILL/scripts/de.py" record-host-heartbeat "$TARGET" --run-id <run-id> --automation-id <host-automation-id> --owner interactive-codex --status active --interval-seconds 900 --last-wakeup-at <timestamp> --last-observed-cursor <event-id> --json
python3 "$DE_SKILL/scripts/de.py" dashboard "$TARGET" --detach --json
python3 "$DE_SKILL/scripts/de.py" dashboard "$TARGET" --status --json
python3 "$DE_SKILL/scripts/de.py" dashboard "$TARGET" --stop --json
python3 "$DE_SKILL/scripts/de.py" cancel "$TARGET" --run-id <run-id> --reason "<reason>" --json
python3 "$DE_SKILL/scripts/de.py" resolve-protocol-violation "$TARGET" --run-id <run-id> --violation <name> --resolution <kind> --rationale "<why>" --evidence "<evidence>" --json
```

`status --json` is the primary summary surface for Codex. Heartbeat checks can
also use `events --since <event-id> --json`, `alerts --json`, and
`resolve-decision --id <decision-id> --option <option-id> --json` after
explicit user approval or an allowed four-heartbeat autonomous technical
fallback. For the autonomous fallback, use:

```bash
python3 "$DE_SKILL/scripts/de.py" resolve-decision "$TARGET" \
  --id <decision-id> \
  --option <option-id> \
  --autonomous-technical \
  --unanswered-heartbeats 4 \
  --autonomous-rationale "<why this is conservative and reversible>" \
  --validation-expected "<validation command>" \
  --json
```

`--autonomous-technical` is a Codex-facing assertion from outer interactive
Codex, not a runtime eligibility engine. Runtime persists and validates the
metadata; `decisions.jsonl` remains the durable audit source, while
`status --json` `autonomous_decisions` is a convenience summary for heartbeat
checks and final reports.

`status --json` also includes `capability_profiles`: registered agent grants,
high-risk modes, pending capability decisions or escalations, and capability
violations. Treat provider-native enforcement as advisory and provider-specific;
the Dispatch Engine contract is the durable profile, prompt snapshot, report
fields, and status/alert/event evidence. A report that exercises
`network_access`, `package_install`, `dependency_resolution`, `docker_socket`,
`service_start`, `test_execution`, `runtime_state_write`, or
`github_issue_create` beyond the grant is a protocol violation unless it links
a decision id.

When triaging completion violations, distinguish truly unregistered completion
from assigned-agent evidence problems. `unregistered_implementation_completion`
means the completed workstream has no assigned or matching implementation agent.
`assigned_implementation_agent_missing` means the workstream names an assigned
agent id with no registry record. `assigned_implementation_agent_invalid_status`
means the assigned or matching agent record exists but is not in a valid
completion status. If the assigned agent completed with an invalid report,
repair the report, scope, or capability diagnostic shown in
`protocol_violations.detected`.

Historical `protocol.violation` events may predate the current event schema.
`alerts --json` normalizes capability-shaped legacy payloads that have no
explicit `violation` into `capability_overreach` alerts and preserves the
original payload in `details.payload` for audit.

If interactive Codex or the coordinator reviews a protocol violation and finds
that it was acknowledged, accepted with concerns, superseded by later
validation, or a false positive, record that audit judgment with
`resolve-protocol-violation`. The command appends to
`.dispatch/runs/<run-id>/protocol-resolutions.jsonl` only after the selector
matches a current protocol violation. Use `--agent-id` and `--workstream` when
`--violation` alone would be ambiguous. `status --json` keeps original
violations visible, adds resolved and unresolved splits plus a
`protocol_violation_resolutions` summary, and uses only unresolved violations
for `next_actions`; `alerts --json` no longer reports a matched resolved
violation as an unresolved protocol alert.

Resolution records are an audit overlay. They do not delete or rewrite the
original event/report evidence, do not mark a terminal run completed, and do
not authorize future workers to exceed their capability profile. Future runs
must still request decisions or narrower scopes before using broader
capabilities.

`status --json` also includes `lifecycle_diagnostics` for material supervision
gaps observed at read time. Treat `missing_agent_launch_evidence`,
`provider_native_spawn_without_report`, `stale_detached_supervisor`,
`orphaned_running_agent`, and `stdout_only_decision_request` diagnostics as
operator-visible blockers. `provider_native_spawn_without_report` means an
active provider-native worker, reviewer, or validator has launch evidence but
no role-specific report after the conservative staleness window; inspect the
provider session, wait only if progress is visible, mark blocked/failed, repair
with durable evidence, or cancel after user approval. These diagnostics are
also surfaced by `alerts --json`; terminal runs may still have empty
`next_actions`, so do not use `next_actions` alone to decide that a detached run
needs no follow-up.

Runtime state is stored under:

```text
.dispatch/plans/
.dispatch/runs/<run-id>/run.json
.dispatch/runs/<run-id>/events.jsonl
.dispatch/runs/<run-id>/decisions.jsonl
.dispatch/runs/<run-id>/protocol-resolutions.jsonl
.dispatch/runs/<run-id>/agents/
.dispatch/runs/<run-id>/prompts/
.dispatch/runs/<run-id>/supervisors/
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/reviews/
.dispatch/runs/<run-id>/validation/
.dispatch/runs/<run-id>/logs/
.dispatch/runs/<run-id>/heartbeats/
.dispatch/runs/<run-id>/dashboard/
```

## Cancelling A Run

Use cancellation only after a user asks interactive Codex to stop a run:

```bash
python3 "$DE_SKILL/scripts/de.py" cancel "$TARGET" --run-id <run-id> --reason "<reason>" --json
```

`--run-id` is optional; when omitted, Dispatch Engine resolves the latest run
under `.dispatch/runs/`. `--reason` is optional and defaults to a user-requested
cancellation message. `de stop` accepts the same flags as a natural-language
alias, but `cancel` is canonical for automation and docs.

Cancellation records a terminal `cancelled` run state, attempts graceful
process termination before escalation, preserves prompts, logs, reports,
events, decisions, reviews, validation, and heartbeat evidence, and marks only
active supervisor/coordinator/worker/reviewer/validator records cancelled with
the same reason. Completed, failed, and already-cancelled agent records keep
their terminal status. Completed and failed runs reject cancellation with a
clear terminal error; already-cancelled runs return idempotent success.

After cancellation, interactive Codex should read:

```bash
python3 "$DE_SKILL/scripts/de.py" status "$TARGET" --run-id <run-id> --json
python3 "$DE_SKILL/scripts/de.py" events "$TARGET" --run-id <run-id> --since <event-id> --json
python3 "$DE_SKILL/scripts/de.py" alerts "$TARGET" --run-id <run-id> --json
```

Then report the cancelled terminal state and reason once, and stop any
host-layer heartbeat for the run after recording
`.dispatch/runs/<run-id>/host-heartbeat.json` with `--status stopped`.

Live coordinator launches write:

```text
.dispatch/runs/<run-id>/prompts/coordinator-001.md
.dispatch/runs/<run-id>/logs/coordinator-001.stdout.log
.dispatch/runs/<run-id>/logs/coordinator-001.stderr.log
```

## Git Guidance

Default: do not commit `.dispatch/` runtime state in target repositories.

Add this to the target repo's `.gitignore` unless that repo has a deliberate fixture policy:

```gitignore
.dispatch/
```

Accepted project changes belong in normal source, test, docs, spec, or configuration paths. Human-curated runbooks, examples, or fixtures can be committed outside `.dispatch/` when the project wants durable documentation.

## Troubleshooting

- `scripts/de.py` missing: reinstall or recopy the whole skill directory; the runtime must live under the skill root.
- `init` fails with invalid plan: check required fields `schema_version`, `plan_id`, `objective`, and a non-empty `workstreams` list.
- `run --dry-run` fails with missing run: import a plan first, or pass `--run-id <run-id>` for an existing run.
- `run` fails because `codex` is unavailable: install or configure the Codex CLI, or use `--provider claude` when the Claude CLI is intentionally available.
- `run --provider claude` fails because `claude` is unavailable: install/configure Claude CLI or use the default Codex provider.
- `cancel` reports `no_run` or `missing_run`: import or select an existing run before cancelling.
- `cancel` reports `run_already_terminal`: completed and failed runs cannot be cancelled; already-cancelled runs return idempotent success.
- `dashboard --detach --json` returns `missing_dashboard_assets`: verify the installed skill root includes `dashboard/index.html` and recopy or reinstall the complete skill root if it does not.
- Dashboard URL opens but progress seems stale: check whether the URL is for an old run id. Use `dashboard --status --run-id <run-id> --json`, then open or report the latest run's `dashboard --detach --json` URL if a continuation run superseded it. Keep using `status --json`, `events --since`, and `alerts --json`; the dashboard is read-only visibility and does not replace heartbeat checks.
- Progress looks stale: check `status`, then `tail`, then inspect `.dispatch/runs/<run-id>/logs/` and `.dispatch/runs/<run-id>/events.jsonl`.
- A capability escalation is pending: read `status --json` `capability_profiles.pending_decisions` and `.pending_escalations`, then resolve the linked decision or narrow/reassign the workstream.
- A protocol alert says `capability_overreach` with `details.source` set to `legacy_protocol_violation_payload`: inspect `details.payload`; the run file was not rewritten, but the alert has been normalized for triage.
- Host wakeups are unavailable: tell the user, "This host cannot create the required Dispatch Engine heartbeat for this thread. The detached run would still write queryable state under `.dispatch/`, but this chat would not be proactively supervised. Please confirm whether to continue without proactive observation or switch to a foreground/debug run."
- A coordinator edited project files directly: treat that as a protocol violation. Reassign implementation to registered workers/reviewers/validators and keep coordinator output as orchestration evidence only.
- Dispatch Engine itself blocks or misguides the workflow: follow `references/issue-reporting-protocol.md` and proactively file or prepare a GitHub issue against `https://github.com/wo1fsea/dispatch-engine/issues`.

## Validation Commands

From the installed skill root:

```bash
python3 scripts/de.py --help
python3 scripts/de.py events --help
python3 scripts/de.py alerts --help
python3 scripts/de.py cancel --help
python3 scripts/de.py dashboard --help
python3 scripts/de.py record-host-heartbeat --help
python3 scripts/de.py stop --help
python3 scripts/de.py resolve-decision --help
python3 scripts/de.py run --help
python3 scripts/de.py version
python3 scripts/de.py run <repo> --dry-run
rg "install|copy|clone|quickstart|.dispatch|status|tail|troubleshooting" README.md SKILL.md references specs/rfc-0013-skill-install-operator-docs
```

`run <repo> --dry-run` requires an imported run in the target repository. If no run exists yet, validate CLI shape with `python3 scripts/de.py run --help` and validate target operation after importing a plan.
