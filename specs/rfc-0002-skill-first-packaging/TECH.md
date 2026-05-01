---
language: en-US
audience: agent
doc_type: spec
---

# Skill-First Packaging Tech Spec

Product spec: `./PRODUCT.md`

## Context

Dispatch Engine was initially described as a local runtime with a possible companion skill. The project direction changed: the repository should itself be a runtime-backed skill so users can copy or clone it directly into a Codex skills directory.

The root must still support public GitHub reading and maintain governance files, but the skill entrypoint and bundled runtime should be first-class.

## Proposed Changes

- Add root `SKILL.md` with `dispatch-engine` metadata and operating workflow.
- Add `agents/openai.yaml` for UI-facing skill metadata.
- Add `scripts/de.py` as the bundled CLI entrypoint.
- Add `scripts/dispatch_engine/` as the initial runtime package.
- Add `references/` for operator, event, and worker protocols.
- Update README and governance context to define Dispatch Engine as a runtime-backed skill.
- Add a smoke-testable minimal CLI supporting `version`, `inspect`, `plan`, and `status`.

## Testing and Validation

- `python scripts/de.py --help`
- `python scripts/de.py version`
- `python scripts/de.py inspect .`
- `python scripts/de.py plan . --objective "smoke test objective"`
- `python scripts/de.py status .`
- Skill structure validation for `SKILL.md`, `agents/openai.yaml`, `scripts/`, and `references/`.

## Risks and Follow-ups

- Risk: The initial runtime is intentionally small and may look more complete than it is. Mitigation: README and specs state that full dispatch is future work.
- Risk: `.dispatch/` smoke-test state could pollute commits. Mitigation: ignore `.dispatch/` and `.out/`.
- Follow-up: Implement real worker adapters and review loops after the packaged runtime shell is stable.
