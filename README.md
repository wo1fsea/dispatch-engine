<!--
language: en-US
audience: mixed
doc_type: router
-->

# Dispatch Engine

Repo-native agent dispatch, with adult supervision.

Dispatch Engine is a runtime-backed Codex skill. The repository root is the installable skill directory, and the local runtime is bundled under `scripts/` so the whole project can be copied or cloned into a Codex skills directory.

The runtime reads a repository's own planning conventions, turns work into schedulable agent workstreams, dispatches worker and reviewer agents serially or in parallel, and keeps progress reviewable.

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
python3 scripts/de.py inspect .
python3 scripts/de.py plan . --objective "smoke test objective"
python3 scripts/de.py status .
python3 scripts/de.py tail .
```

## Current Direction

- Respect target repository conventions instead of prescribing a universal spec format.
- Keep orchestration state explicit, resumable, and reviewable.
- Use interactive agents as supervisors and operators, not as hidden long-running runtimes.
- Support pluggable adapters for planning sources, status sinks, validation commands, and worker agents.
- Keep the runnable runtime bundled inside the skill directory before recommending copy/clone installation.

This repository is intentionally small while the project shape is being designed.

## Governance

Agent and contributor routing starts in [`AGENTS.md`](AGENTS.md). Detailed workflows live under [`docs/governance/`](docs/governance/).
