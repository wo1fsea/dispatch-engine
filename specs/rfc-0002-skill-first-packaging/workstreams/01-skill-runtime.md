---
id: 01-skill-runtime
language: en-US
audience: agent
doc_type: spec
status: validated
owner: codex
branch: main
pr:
files:
  - SKILL.md
  - agents/**
  - scripts/**
  - references/**
  - README.md
  - docs/governance/**
  - specs/rfc-0002-skill-first-packaging/**
depends_on: []
claimed_at: 2026-05-01T00:00:00+08:00
lease_expires_at:
updated: 2026-05-01
---

# Skill Runtime Workstream

## Scope

Reorganize the repository so the root is an installable skill with a bundled runtime.

## Plan

1. Add root skill metadata and operator instructions.
2. Add initial runtime CLI and package under `scripts/`.
3. Add protocol references.
4. Update README and governance context.
5. Validate skill shape and runtime smoke commands.

## Progress

- Added root `SKILL.md`.
- Added `agents/openai.yaml`.
- Added initial `scripts/de.py` CLI and runtime package.
- Added operator, event, and worker protocol references.
- Updated README and governance context for skill-first packaging.
- Added `.dispatch/` and Python cache ignores.

## Validation

- `python scripts/de.py --help`
- `python scripts/de.py version`
- `python scripts/de.py inspect .`
- `python scripts/de.py plan . --objective "smoke test objective"`
- `python scripts/de.py status .`
- Manual skill structure check for `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/`.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-01 codex: claimed and started skill-first packaging workstream.
- 2026-05-01 codex: implemented and validated root skill packaging.
