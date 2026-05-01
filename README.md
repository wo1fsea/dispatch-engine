<!--
language: en-US
audience: mixed
doc_type: router
-->

# Dispatch Engine

Repo-native agent dispatch, with adult supervision.

Dispatch Engine is a runtime-backed Codex skill. The repository root is the installable skill directory, and the local runtime is bundled under `scripts/` so the whole project can be copied or cloned into a Codex skills directory.

Interactive Codex reads a repository's own planning conventions, turns work into an explicit dispatch plan, reviews results, and keeps the user in the loop. The runtime imports that explicit plan, stores durable `.dispatch/` state, exposes status/tail readers, and is the future home of the mechanical scheduler, worker, reviewer, and validation loop.

Dispatch Engine-generated non-project runtime content belongs under `.dispatch/` in the target repository. Project files changed for the user's objective stay in the target repository's normal source, test, docs, spec, or configuration paths.

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

Basic smoke checks:

```bash
python3 scripts/de.py --help
python3 scripts/de.py version
python3 scripts/de.py status .
python3 scripts/de.py tail .
```

## Current Direction

- Respect target repository conventions instead of prescribing a universal spec format.
- Keep orchestration state explicit, resumable, and reviewable.
- Use interactive Codex plus the skill for repository discovery, planning, review, validation judgment, and user interaction.
- Use the runtime for explicit plan import, `.dispatch/` state, event logs, status/tail, and future mechanical orchestration.
- Support pluggable adapters for worker agents, reviewer agents, validation runners, and status sinks.
- Keep the runnable runtime bundled inside the skill directory before recommending copy/clone installation.

This repository is intentionally small while the project shape is being designed.

## Governance

Agent and contributor routing starts in [`AGENTS.md`](AGENTS.md). Detailed workflows live under [`docs/governance/`](docs/governance/).
