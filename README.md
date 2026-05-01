<!--
language: en-US
audience: mixed
doc_type: router
-->

# Dispatch Engine

Repo-native agent dispatch, with adult supervision.

Dispatch Engine is a local orchestration runtime that reads a repository's own planning conventions, turns work into schedulable agent workstreams, dispatches worker and reviewer agents serially or in parallel, and keeps progress reviewable.

## Current Direction

- Respect target repository conventions instead of prescribing a universal spec format.
- Keep orchestration state explicit, resumable, and reviewable.
- Use interactive agents as supervisors and operators, not as hidden long-running runtimes.
- Support pluggable adapters for planning sources, status sinks, validation commands, and worker agents.

This repository is intentionally small while the project shape is being designed.

## Governance

Agent and contributor routing starts in [`AGENTS.md`](AGENTS.md). Detailed workflows live under [`docs/governance/`](docs/governance/).
