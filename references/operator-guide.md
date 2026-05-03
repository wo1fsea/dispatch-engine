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

Detached runs do not automatically wake the foreground Codex chat. After every
successful interactive `run --detach`, interactive Codex must create a
host-layer thread heartbeat when the current host supports wakeups. The
heartbeat wakes Codex, and Codex then reads Dispatch Engine state and reports
only material changes. When the run completes, fails, or is cancelled, Codex
must stop the heartbeat. Dispatch Engine does not send chat messages or own the
host wakeup. The default heartbeat interval is 15 minutes. If the same pending
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

The provider process launched by `de run` is a coordinator only. It may plan, dispatch, monitor, summarize, request decisions, and write Dispatch Engine runtime state under `.dispatch/`, but it must not directly implement project-file changes. Project implementation belongs to registered workers, reviewers, or validators using provider-native spawn mechanisms, normalized capability profiles, and the shared `.dispatch/` observability contract.

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
python3 "$DE_SKILL/scripts/de.py" cancel "$TARGET" --run-id <run-id> --reason "<reason>" --json
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

Runtime state is stored under:

```text
.dispatch/plans/
.dispatch/runs/<run-id>/run.json
.dispatch/runs/<run-id>/events.jsonl
.dispatch/runs/<run-id>/decisions.jsonl
.dispatch/runs/<run-id>/agents/
.dispatch/runs/<run-id>/prompts/
.dispatch/runs/<run-id>/supervisors/
.dispatch/runs/<run-id>/reports/
.dispatch/runs/<run-id>/reviews/
.dispatch/runs/<run-id>/validation/
.dispatch/runs/<run-id>/logs/
.dispatch/runs/<run-id>/heartbeats/
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
host-layer heartbeat for the run.

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
- Progress looks stale: check `status`, then `tail`, then inspect `.dispatch/runs/<run-id>/logs/` and `.dispatch/runs/<run-id>/events.jsonl`.
- A capability escalation is pending: read `status --json` `capability_profiles.pending_decisions` and `.pending_escalations`, then resolve the linked decision or narrow/reassign the workstream.
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
python3 scripts/de.py stop --help
python3 scripts/de.py resolve-decision --help
python3 scripts/de.py run --help
python3 scripts/de.py version
python3 scripts/de.py run <repo> --dry-run
rg "install|copy|clone|quickstart|.dispatch|status|tail|troubleshooting" README.md SKILL.md references specs/rfc-0013-skill-install-operator-docs
```

`run <repo> --dry-run` requires an imported run in the target repository. If no run exists yet, validate CLI shape with `python3 scripts/de.py run --help` and validate target operation after importing a plan.
