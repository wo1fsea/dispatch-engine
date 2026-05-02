---
language: en-US
audience: agent
doc_type: spec
---

# Skill Install Operator Docs Tech Spec

## Proposed Changes

- Update `README.md`, `SKILL.md`, and `references/operator-flow.md`.
- Add `references/operator-guide.md` as the full install and target repo runbook.
- Add install/copy/clone guidance.
- Add target repo quickstart.
- Add `.dispatch/` ignore/commit guidance.
- Add known limitations and troubleshooting.

## Workstreams

1. `01-install-docs`: install and smoke checks.
2. `02-operator-quickstart`: target repo flow and common commands.
3. `03-troubleshooting-validation`: known limits and docs validation.

## Validation

```bash
python3 scripts/de.py --help
python3 scripts/de.py run --help
python3 scripts/de.py version
rg "install|copy|clone|quickstart|.dispatch|status|tail|troubleshooting" README.md SKILL.md references specs/rfc-0013-skill-install-operator-docs
git diff --check
```
