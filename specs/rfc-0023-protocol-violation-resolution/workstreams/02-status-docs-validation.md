---
workstream_id: "02"
spec_id: rfc-0023-protocol-violation-resolution
language: en-US
audience: agent
doc_type: workstream
status: completed
owner: codex
updated: 2026-05-04
---

# Workstream 02: Status, Alerts, Docs, And Validation

## Scope

Overlay resolution records onto status and alerts, document the operator
protocol, and validate the dogfood issue shape.

## Activity Log

- 2026-05-04 codex: overlaid protocol resolutions onto `status --json`,
  `next_actions`, and `alerts --json` while preserving original violation
  evidence.
- 2026-05-04 codex: normalized legacy `protocol.violation` payloads with
  `kind: capability_overreach` and updated operator/heartbeat guidance.
- 2026-05-04 codex: ran focused tests, full unittest discovery, CLI help
  smoke checks, and `git diff --check`.

## Acceptance

- `status --json` exposes protocol violation resolution summaries and
  resolved/unresolved splits.
- `next_actions` counts unresolved protocol violations only.
- `alerts --json` no longer emits unresolved protocol violation alerts for
  matched resolved violations.
- Legacy event payloads with `kind: capability_overreach` normalize to
  `capability_overreach`.
- Operator/heartbeat guidance explains when and how interactive Codex should
  record a resolution.
- Focused and full test suites pass.

## Non-goals

- Marking terminal runs complete.
- Hiding or rewriting historical protocol violation evidence.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
git diff --check
```
