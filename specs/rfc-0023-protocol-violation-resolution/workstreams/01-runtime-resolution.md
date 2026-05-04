---
workstream_id: "01"
spec_id: rfc-0023-protocol-violation-resolution
language: en-US
audience: agent
doc_type: workstream
status: completed
owner: codex
updated: 2026-05-04
---

# Workstream 01: Runtime Resolution Records And CLI

## Scope

Implement append-only protocol-violation resolution records and the
Codex-facing command that writes them.

## Activity Log

- 2026-05-04 codex: added `protocol-resolutions.jsonl` append-only records,
  conservative selector matching, resolution-kind validation, and
  `resolve-protocol-violation`.
- 2026-05-04 codex: added regression coverage for successful writes,
  ambiguous selectors, and invalid resolution kinds.

## Acceptance

- Resolution records are written to
  `.dispatch/runs/<run-id>/protocol-resolutions.jsonl`.
- The runtime validates resolution kind, selector, rationale, evidence, actor,
  and run id.
- The command fails when the selector does not match a current protocol
  violation.
- The command returns JSON suitable for interactive Codex.
- Regression tests cover successful writes, invalid selectors, and invalid
  resolution kinds.

## Non-goals

- Coordinator re-entry.
- Automatic run status transitions.
- Editing or deleting historical violation evidence.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail tests.test_codex_facing_control_surface
python3 scripts/de.py resolve-protocol-violation --help
```
