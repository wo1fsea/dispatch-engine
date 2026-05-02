---
workstream_id: 02-worker-prompt-template
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex
branch: main
updated: 2026-05-02
depends_on:
  - 01-worker-state-report-protocol
---

# Worker Prompt Template

## Scope

Add centralized worker prompt rendering so runtime code does not embed worker prompt text inline.

## Files

- `references/prompts/worker-protocol.md`
- `scripts/dispatch_engine/prompts.py`
- `tests/test_worker_adapter_protocol.py`

## Requirements

- Store the worker prompt template under `references/prompts/`.
- Render target repo, run id, state directory, workstream id/title/scope, assigned files, allowed write roots, dependency context, validation expectations, and report path.
- Tell workers they are not alone in the codebase and must respect other workstreams.
- Tell workers not to modify files outside assigned scope unless a recorded decision expands scope.
- Include the required report JSON shape.
- Write prompt snapshots under `.dispatch/runs/<run-id>/prompts/<agent-id>.md`.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
rg "not alone|assigned files|allowed write roots|report" references/prompts/worker-protocol.md
git diff --check
```

Evidence recorded on 2026-05-02:

- Added `references/prompts/worker-protocol.md` as the centralized worker prompt template.
- Added `render_worker_prompt` in `scripts/dispatch_engine/prompts.py`.
- Added `write_worker_prompt_snapshot` so rendered worker prompts are recorded under `.dispatch/runs/<run-id>/prompts/<agent-id>.md`.
- Added focused tests confirming repo, run id, state dir, workstream, assigned files, allowed write roots, validation, report path, report JSON contract, and "not alone in the codebase" constraints render into the prompt.
- Coordinator review added a prompt snapshot assertion after finding the initial worker result rendered but did not write the prompt snapshot.
- `PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol` passed, 7 tests.
