---
language: en-US
audience: agent
doc_type: workstream
---

# Runtime Launch Args

## Scope

Implement high-permission coordinator launch arguments for Codex and Claude
provider profiles.

## Tasks

- Add Codex `--sandbox danger-full-access` to dry-run and live launch argv.
- Add Claude `--dangerously-skip-permissions --permission-mode bypassPermissions` to dry-run and live launch argv.
- Keep prompt-file instruction behavior unchanged.
- Keep coordinator registry write scope as `.dispatch/`.
- Update focused unit tests.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_run_dry_run
PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision
```
