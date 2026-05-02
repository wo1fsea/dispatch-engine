<!--
language: en-US
audience: mixed
doc_type: router
-->

# Dispatch Engine

Repo-native agent dispatch, with adult supervision.

Dispatch Engine is a runtime-backed Codex skill. The repository root is the installable skill directory, and the local runtime is bundled under `scripts/` so the whole project can be copied or cloned into a Codex skills directory.

Interactive Codex reads a repository's own planning conventions, turns work into an explicit dispatch plan, reviews results, and keeps the user in the loop. The runtime imports that explicit plan, stores durable `.dispatch/` state, exposes status/tail readers, and can launch a foreground provider CLI coordinator for the imported run.

Dispatch Engine-generated non-project runtime content belongs under `.dispatch/` in the target repository. Project files changed for the user's objective stay in the target repository's normal source, test, docs, spec, or configuration paths.

## Install As A Skill

The repository root is the installable skill. Keep `SKILL.md`, `references/`,
`references/prompts/`, and the bundled runtime under `scripts/` together.

Clone or copy the whole root into a Codex skills directory:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
git clone <dispatch-engine-repo-url> "$CODEX_HOME/skills/dispatch-engine"
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
install, quickstart, status, and troubleshooting runbook.

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
```

Target repo smoke checks after importing a plan:

```bash
python3 scripts/de.py run <repo> --dry-run
python3 scripts/de.py run <repo> --provider codex --dry-run
python3 scripts/de.py run <repo> --provider claude --dry-run
python3 scripts/de.py status <repo>
python3 scripts/de.py tail <repo>
```

`de run <repo>` launches a foreground provider CLI coordinator for the latest
imported run. Omitting `--provider` defaults to provider `codex`, which uses a
`codex exec` command shape; `--provider codex` selects that same provider
explicitly. `--provider claude` uses a Claude coordinator command shape based on
`claude -p`.

Target repo quickstart:

```bash
DE_SKILL="${CODEX_HOME:-$HOME/.codex}/skills/dispatch-engine"
TARGET=/path/to/target-repo
mkdir -p "$TARGET/.dispatch/plans"
$EDITOR "$TARGET/.dispatch/plans/plan-001.json"
python3 "$DE_SKILL/scripts/de.py" init "$TARGET" --plan "$TARGET/.dispatch/plans/plan-001.json"
python3 "$DE_SKILL/scripts/de.py" run "$TARGET" --dry-run
python3 "$DE_SKILL/scripts/de.py" run "$TARGET"
python3 "$DE_SKILL/scripts/de.py" status "$TARGET"
python3 "$DE_SKILL/scripts/de.py" tail "$TARGET"
```

Interactive Codex remains the external operator: it reads target repo
instructions, prepares the explicit plan, keeps the user in the loop, asks for
decisions, reviews evidence, and polls `status` / `tail`. Dispatch Engine's
provider CLI coordinator performs provider-native dispatch and writes durable
`.dispatch/` orchestration state, but it is coordinator-only and does not
directly implement project files.

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

Provider CLI coordinators are coordinator-only. They may plan, dispatch,
monitor, summarize, request decisions, and write Dispatch Engine runtime state,
but they must not directly implement project-file changes. Workers, reviewers,
and validators must be registered in `.dispatch/runs/<run-id>/agents/` before
their implementation, review, or validation output is accepted.
Coordinator owns spawn decisions; Dispatch Engine owns the durable
observability contract for every spawned agent.

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
- Use the runtime for explicit plan import, live coordinator launch, `.dispatch/` state, event logs, status/tail, and future mechanical orchestration.
- Use `.dispatch/runs/<run-id>/agents/`, `prompts/`, `reports/`, `reviews/`, `validation/`, `logs/`, and `heartbeats/` for observable coordinator, worker, reviewer, and validator state.
- Use lifecycle events such as `coordinator.started`, `coordinator.completed`, `coordinator.failed`, `agent.spawned`, `workstream.assigned`, `agent.heartbeat`, `agent.completed`, `agent.failed`, and `protocol.violation` to keep status resumable from files instead of chat memory.
- Keep runtime prompt templates centralized in `references/prompts/`.
- Treat worker output as valid only when a registered worker has a durable report under `.dispatch/runs/<run-id>/reports/`; reviewer evidence belongs under `reviews/`, validator evidence belongs under `validation/`, and missing or malformed evidence is a protocol violation.
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
