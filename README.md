<!--
language: en-US
audience: mixed
doc_type: router
-->

# Dispatch Engine

Repo-native agent dispatch, with adult supervision.

Dispatch Engine is a runtime-backed Codex skill. The repository root is the installable skill directory, and the local runtime is bundled under `scripts/` so the whole project can be copied or cloned into a Codex skills directory.

Project repository: [wo1fsea/dispatch-engine](https://github.com/wo1fsea/dispatch-engine).
Report framework, skill, runtime, protocol, heartbeat, prompt, status, or
process blocker issues to [Dispatch Engine issues](https://github.com/wo1fsea/dispatch-engine/issues).

Interactive Codex reads a repository's own planning conventions, turns work into an explicit dispatch plan, reviews results, and keeps the user in the loop. The runtime imports that explicit plan, stores durable `.dispatch/` state, exposes status/tail readers, and can launch a foreground or detached provider CLI coordinator for the imported run.

The `de` CLI is a Codex-facing machine interface, not the human user interface.
Humans talk to interactive Codex; Codex calls `de`, reads JSON/file state, and
explains progress or decisions.

Dispatch Engine-generated non-project runtime content belongs under `.dispatch/` in the target repository. Project files changed for the user's objective stay in the target repository's normal source, test, docs, spec, or configuration paths.

## Install As A Skill

The repository root is the installable skill. Keep `SKILL.md`, `references/`,
`references/prompts/`, and the bundled runtime under `scripts/` together.

Clone or copy the whole root into a Codex skills directory:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
git clone https://github.com/wo1fsea/dispatch-engine.git "$CODEX_HOME/skills/dispatch-engine"
cd "$CODEX_HOME/skills/dispatch-engine"
python3 scripts/de.py --help
python3 scripts/de.py version
```

For a local copy install:

```bash
SOURCE=/path/to/dispatch-engine
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills/dispatch-engine"
rsync -a --delete --exclude '.git/' --exclude '.dispatch/' "$SOURCE/" "$CODEX_HOME/skills/dispatch-engine/"
```

See [`references/operator-guide.md`](references/operator-guide.md) for the full
install, quickstart, status, and troubleshooting runbook. See
[`references/heartbeat-observation.md`](references/heartbeat-observation.md)
for detached-run heartbeat guidance. See
[`references/issue-reporting-protocol.md`](references/issue-reporting-protocol.md)
for proactive GitHub issue reporting when Dispatch Engine itself blocks or
misguides a workflow.

## Skill Layout

```text
SKILL.md                    # Codex skill entrypoint
agents/openai.yaml          # UI metadata
scripts/de.py               # bundled CLI entrypoint
scripts/dispatch_engine/    # bundled runtime package
references/                 # operator and protocol guidance
docs/governance/            # repository development governance
specs/                      # project specs
```

CLI availability smoke checks from the skill root:

```bash
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py run --help
python3 scripts/de.py cancel --help
python3 scripts/de.py stop --help
```

Target repo smoke checks after importing a plan:

```bash
python3 scripts/de.py run <repo> --dry-run
python3 scripts/de.py run <repo> --detach
python3 scripts/de.py run <repo> --provider codex --dry-run
python3 scripts/de.py run <repo> --provider claude --dry-run
python3 scripts/de.py status <repo>
python3 scripts/de.py tail <repo>
```

`de run <repo>` launches a foreground provider CLI coordinator for the latest
imported run. `de run <repo> --detach` starts a background supervisor and
returns immediately, which is the preferred interactive Codex operation mode.
Omitting `--provider` defaults to provider `codex`, which uses a `codex exec`
command shape with `--sandbox danger-full-access`; `--provider codex` selects
that same provider explicitly. `--provider claude` uses a Claude coordinator
command shape based on
`claude --dangerously-skip-permissions --permission-mode bypassPermissions -p`.

Detached runs keep the chat responsive, but they do not automatically wake the
foreground Codex chat. After every successful interactive `run --detach`,
interactive Codex must create a host-layer thread heartbeat when the host
supports wakeups. The heartbeat wakes Codex, which then reads `status --json`,
`events --since` deltas, and `alerts --json` snapshots before reporting
material changes. When the run completes, fails, or is cancelled, Codex must
stop the heartbeat. The default heartbeat interval is 15 minutes. Dispatch
Engine does not send chat messages or own the wakeup. If the same technical
decision remains unanswered across four consecutive heartbeat checks, outer
Codex plus the heartbeat owns the eligibility judgment and may choose a
conservative, reversible option. Dispatch Engine runtime does not decide
eligibility or pick the option; it only persists and validates the structured
metadata. Record the choice with `resolve-decision --autonomous-technical`,
which uses actor `interactive-codex-autonomous`, appends the source-of-truth
entry to `.dispatch/runs/<run-id>/decisions.jsonl`, and makes a compact
`status --json` `autonomous_decisions` summary available for final reporting.

When the user asks to stop a Dispatch Engine run, interactive Codex should call
`de cancel <repo> --run-id <run-id> --reason <text> --json`. The command
resolves the latest run when `--run-id` is omitted, records a durable terminal
`cancelled` state, attempts graceful process termination before escalation,
preserves `.dispatch/` evidence, and marks active supervisor/coordinator/agent
records cancelled with the same reason. `de stop` is an alias for natural
language, while `cancel` remains canonical. Cancellation is not a failure;
after cancelling, Codex should read `status --json`, `events --since`, and
`alerts --json`, report the reason once, and stop any host heartbeat for the
run.

Target repo quickstart:

```bash
DE_SKILL="${CODEX_HOME:-$HOME/.codex}/skills/dispatch-engine"
TARGET=/path/to/target-repo
mkdir -p "$TARGET/.dispatch/plans"
$EDITOR "$TARGET/.dispatch/plans/plan-001.json"
python3 "$DE_SKILL/scripts/de.py" init "$TARGET" --plan "$TARGET/.dispatch/plans/plan-001.json"
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --dry-run
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --detach
python3 "$DE_SKILL/scripts/de.py" status "$TARGET"
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET"
python3 "$DE_SKILL/scripts/de.py" status "$TARGET"
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET"
```

Interactive Codex remains the external operator: it reads target repo
instructions, prepares the explicit plan, keeps the user in the loop, asks for
decisions, reviews evidence, and polls Codex-facing state surfaces such as
`status --json`, `events --since`, `alerts --json`, and `tail`. After explicit
user approval, Codex can use `resolve-decision` to record a selected option.
After an allowed four-heartbeat autonomous technical fallback, Codex records
the selected option with the Codex-facing autonomous flags:

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

Dispatch Engine's provider CLI coordinator
performs provider-native dispatch and writes durable `.dispatch/`
orchestration state, but it is coordinator-only and does not directly implement
project files.

`de run <repo> --dry-run` renders the selected provider command and coordinator
prompt without launching a provider process or writing runtime state. Live runs
write:

```text
.dispatch/runs/<run-id>/prompts/coordinator-001.md
.dispatch/runs/<run-id>/logs/coordinator-001.stdout.log
.dispatch/runs/<run-id>/logs/coordinator-001.stderr.log
```

Live runs register `coordinator-001` under
`.dispatch/runs/<run-id>/agents/`, move its status from `running` to
`completed` or `failed`, and emit `coordinator.started` followed by
`coordinator.completed` or `coordinator.failed`.
The provider process receives a short instruction pointing to the recorded
prompt snapshot path; the full coordinator prompt is not embedded directly in
the launch command.

Provider CLI coordinators are coordinator-only. Dispatch Engine launches the
coordinator with high provider permissions so it can spawn agents, install
dependencies, validate work, and inspect repo state. Coordinators may plan,
dispatch, monitor, summarize, request decisions, and write Dispatch Engine
runtime state, but they must not directly implement project-file changes.
Workers, reviewers, and validators must be registered in
`.dispatch/runs/<run-id>/agents/` before their implementation, review, or
validation output is accepted. Coordinator owns spawn decisions and decides
worker permission scope through assigned files, allowed write roots,
normalized capability profiles, and provider-native worker launch options;
Dispatch Engine owns the durable observability contract for every spawned
agent. Provider Worker Launch requires actual provider-native spawn evidence
or codex CLI fallback evidence before `agent.spawned` or `running`;
registration alone is not launch evidence.

Capability profiles make non-file authority auditable without pretending to be
a provider-independent sandbox. Omitted workstream profiles normalize to
`worker-standard`; registered reviewers and validators default to
`reviewer-standard` and `validator-standard`. Profiles cover `network_access`,
`package_install`, `dependency_resolution`, `docker_socket`, `service_start`,
`test_execution`, `runtime_state_write`, and `github_issue_create`, with repo
write scope embedded as assigned files and allowed write roots. Agent prompts
render the grant, worker reports declare `capability_profile_id`,
`capabilities_exercised`, and `capability_escalations`, and `status --json`
exposes `capability_profiles` with active grants, high-risk modes, pending
escalation decisions, and violations. Provider-native enforcement remains
provider-specific; Dispatch Engine owns the durable state, prompt, report,
status, and protocol violation contract.
Imported workstreams may include `validation_warnings` when validation commands
appear inconsistent with the normalized profile, prompting the coordinator to
narrow validation, request a decision, or block before dispatch.

Runtime prompt templates live under `references/prompts/`. Runtime modules
should load and render those templates instead of embedding prompt text inline.
The coordinator prompt template records the coordinator-only spawn contract and
is written as a run-scoped snapshot before provider launch; the provider command
receives only a short file-path instruction. The worker prompt template records
the target repo, run id, state directory, assigned workstream, file scope,
validation expectations, and report path.

## Architecture Principle

Dispatch Engine is skill-first and runtime-when-necessary. Put workflow
judgment, role behavior, provider-native spawn guidance, review criteria, validation
expectations, and operator runbooks in `SKILL.md`, `references/`, and
`references/prompts/` by default. Move behavior into `scripts/dispatch_engine/`
only when it must be durable, queryable, resumable, mechanically validated, or
reported through `de status` / `de tail`.

The runtime should stay small: explicit plan import, `.dispatch/` state,
prompt-template rendering, coordinator launch, event logs, status/tail readers,
and conservative protocol checks. Provider-specific orchestration mechanics
belong in coordinator guidance or adapters until dogfood proves runtime code is
necessary.

## Current Direction

- Respect target repository conventions instead of prescribing a universal spec format.
- Keep orchestration state explicit, resumable, and reviewable.
- Use interactive Codex plus the skill for repository discovery, planning, review, validation judgment, and user interaction.
- Use the runtime for explicit plan import, foreground or detached coordinator launch, user-requested cancellation, `.dispatch/` state, event logs, status/tail, and future mechanical helpers.
- Treat host heartbeat/wakeup automation as the required observation trigger for proactive chat updates after interactive detached launches; Dispatch Engine writes queryable state but does not wake or message the chat directly.
- Keep autonomous technical decision eligibility in outer interactive Codex and heartbeat guidance. Runtime only validates supplied metadata, appends records to `decisions.jsonl`, emits normal decision events, and surfaces `status --json` summaries.
- Use `.dispatch/runs/<run-id>/agents/`, `prompts/`, `supervisors/`, `reports/`, `reviews/`, `validation/`, `logs/`, and `heartbeats/` for observable coordinator, worker, reviewer, and validator state.
- Use lifecycle events such as `coordinator.started`, `coordinator.completed`, `coordinator.failed`, `agent.spawned`, `workstream.assigned`, `agent.heartbeat`, `agent.completed`, `agent.failed`, `protocol.violation`, `capability.profile.granted`, `capability.escalation.requested`, `capability.escalation.resolved`, `capability.violation`, `run.cancel.requested`, `run.cancel.signal`, and `run.cancel.completed` to keep status resumable from files instead of chat memory.
- Keep runtime prompt templates centralized in `references/prompts/`.
- Treat worker output as valid only when a registered worker has a durable report under `.dispatch/runs/<run-id>/reports/`; reviewer evidence belongs under `reviews/`, validator evidence belongs under `validation/`, and missing or malformed evidence is a protocol violation.
- Treat capability overreach in agent reports as a protocol violation unless the exercised capability links to a recorded decision id.
- Validator report statuses are `passed`, `failed`, `blocked`, and `skipped`; validators should not write `completed`, and `status --json` reports schema repair actions when validator evidence needs field-level fixes.
- Treat coordinator-spawned and adapter-spawned agents the same for registration, prompt snapshots, reports, logs, status, heartbeats, events, and violations.
- Support pluggable adapters for worker agents, reviewer agents, validation runners, and status sinks.
- Keep the runnable runtime bundled inside the skill directory before recommending copy/clone installation.

This repository is intentionally small while the project shape is being designed.

## Target Repo Git Guidance

Default target repository policy:

```gitignore
.dispatch/
```

Do not commit generated run state, logs, prompt snapshots, reports, heartbeats,
or imported plans unless the target repository has an explicit fixture policy.
Accepted project work belongs in normal source, test, docs, spec, or
configuration paths.

## Governance

Agent and contributor routing starts in [`AGENTS.md`](AGENTS.md). Detailed workflows live under [`docs/governance/`](docs/governance/).
