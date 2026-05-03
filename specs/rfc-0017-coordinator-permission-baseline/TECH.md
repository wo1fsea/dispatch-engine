---
language: en-US
audience: agent
doc_type: spec
---

# Coordinator Permission Baseline Tech Spec

## Design

The provider profile in `scripts/dispatch_engine/coordinators.py` is the source
of truth for coordinator launch permission flags. `_render_argv()` uses the
profile for both dry-run and live execution, so previews and actual launches
cannot drift.

Codex profile:

```text
codex exec --sandbox danger-full-access --cd <repo-root> "Read and follow the Dispatch Engine coordinator instructions in this file: <prompt-file>"
```

Claude profile:

```text
claude --dangerously-skip-permissions --permission-mode bypassPermissions -p "Read and follow the Dispatch Engine coordinator instructions in this file: <prompt-file>"
```

The coordinator registry record remains intentionally narrow:

```json
{
  "role": "coordinator",
  "allowed_write_roots": [".dispatch/"],
  "assigned_files": []
}
```

That registry record is a Dispatch Engine protocol boundary, not an operating
system sandbox. The high-permission provider launch lets the coordinator
coordinate real work; the protocol still marks coordinator-authored
project-file implementation as invalid unless an explicit recorded decision
allows it.

Worker permission scope remains coordinator-owned. Dispatch Engine validates
the durable evidence it receives:

- worker prompt includes assigned files and allowed write roots
- worker report lists changed files
- report validation rejects changed files outside the assigned scope
- permission expansions require a recorded decision

## Implementation Tasks

1. Add provider-profile coordinator permission args.
2. Render Codex and Claude high-permission argv from the same profile in dry-run and live launch.
3. Update unit tests for dry-run and fake-provider live supervision.
4. Update skill/reference docs and centralized prompt templates.
5. Record the baseline in this spec and keep broader worker capability profiles for a future spec if needed.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_run_dry_run
PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py run --help
git diff --check
```
