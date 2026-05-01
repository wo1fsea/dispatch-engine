---
language: en-US
audience: agent
doc_type: normative
---

# Temp Artifacts

Temporary artifacts are useful during work, but they must not pollute formal repo knowledge.

## Default Directory

Use `.out/` by default:

```text
.out/
  screenshots/
  recordings/
  traces/
  logs/
  reports/
  scratch/
```

`.out/` should be gitignored unless the repo has a stronger local convention.

## Artifact Classes

- `ephemeral`: temporary debugging output. Default: do not commit.
- `evidence`: validation evidence referenced by a PR, spec, or workstream. Default: cite the path, do not commit.
- `promoted`: artifact that must be retained long term. Move it into an owned docs/spec location.

## Rules

- Put temporary artifacts in `.out/`.
- Do not commit `.out/` by default.
- Evidence can be referenced without being committed.
- Promote long-term artifacts into owned locations such as `docs/assets/`, `docs/reports/`, or `specs/<spec-id>/evidence/`.
- Do not place unpromoted artifacts in repo root, `docs/`, `specs/`, `src/`, or `tests/`.
- Raw agent drafts stay in `.out/scratch/` until explicitly accepted.
- Cleanup is part of done.
- Do not write secrets, tokens, private customer data, or sensitive logs into `.out/`.

## Reporting

```markdown
## Temp Artifacts

- Created:
- Referenced as evidence:
- Promoted:
- Cleaned:
- Intentionally retained:
```
