---
language: en-US
audience: agent
doc_type: spec
---

# Protocol Violation Resolution Tech Spec

Product spec: `./PRODUCT.md`

## Implementation Context

Issue #19 came from a dogfood run where product validation was later repaired
and confirmed, but the original run had no Dispatch Engine command to record
that protocol-violation alerts had been reviewed or superseded. Status could
only show a generic `repair_protocol_violations` action.

Relevant current files:

- `scripts/dispatch_engine/cli.py`: command registration and JSON output.
- `scripts/dispatch_engine/state.py`: status, alerts, next actions, and event
  protocol violation normalization.
- `scripts/dispatch_engine/events.py`: event helpers.
- `tests/test_status_tail.py` and
  `tests/test_codex_facing_control_surface.py`: status/alert regressions.
- `references/operator-guide.md`,
  `references/heartbeat-observation.md`, and prompt references if guidance
  changes.

## Change Gate

- Problem: Operators can resolve the real target-repo blocker, but Dispatch
  Engine has no durable audit surface to resolve or supersede protocol alerts.
- Existing path considered: Cancel the run and preserve evidence.
- Why existing path is insufficient: Cancellation is honest for the terminal
  dogfood run, but it cannot express reviewed protocol violations or prevent
  stale heartbeat/status loops for active runs.
- Smallest new surface: One append-only resolution record, one CLI command,
  and status/alerts overlay logic.
- What will be deleted or replaced: No evidence files are deleted; only
  unresolved counts and next-action logic change.
- Owner: Dispatch Engine maintainers.
- Validation: focused status/CLI tests, full unittest discovery, CLI help,
  `git diff --check`, and dogfood status read against issue #19 run id.
- Temporary or permanent: Permanent observability and audit surface.
- Removal condition: Superseded by a richer protocol evidence ledger that
  preserves this resolution information.

## Proposed Changes

1. Add protocol resolution persistence.
   - Store append-only records under
     `.dispatch/runs/<run-id>/protocol-resolutions.jsonl`.
   - Provide a small runtime helper that validates resolution kind, selector,
     rationale, evidence, actor, and timestamp.
   - Match selectors against current protocol violations before writing.
2. Add a Codex-facing CLI command.
   - Command shape:
     `de resolve-protocol-violation <repo> --run-id <run-id> --violation <name> --resolution <kind> --rationale <text> --evidence <text> [--agent-id <id>] [--workstream <id>] [--actor <actor>] --json`
   - The command writes the append-only record and returns the matched
     violation plus resolution record.
   - Non-JSON output should be concise and Codex-readable.
3. Overlay resolutions in status and alerts.
   - `status --json` adds a `protocol_violation_resolutions` summary.
   - `protocol_violations` keeps `detected`, `event_count`, and
     `detected_count`, and adds `resolved_count`, `unresolved_count`,
     `resolved`, and `unresolved`.
   - `next_actions` uses unresolved count only.
   - `alerts --json` should not emit unresolved protocol alerts for resolved
     violations; it may expose resolution metadata for audit if useful.
4. Normalize legacy event payloads using `payload.kind`.
   - If a `protocol.violation` event lacks `violation` but has
     `kind: capability_overreach`, normalize it as `capability_overreach`.
   - Preserve the original payload in details.
5. Update skill/operator guidance.
   - Document when interactive Codex should resolve a protocol violation:
     after review, with rationale, evidence, and any validation that supersedes
     the violation.
   - Clarify that resolution does not authorize workers to exceed capability
     profiles in future runs.

## Validation Plan

Run:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_status_tail tests.test_codex_facing_control_surface
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py resolve-protocol-violation --help
python3 scripts/de.py status --help
python3 scripts/de.py alerts --help
git diff --check
```

Dogfood read-only check:

```bash
python3 scripts/de.py status "/Users/huangquanyong/Projects/ObsidianVault/02 Engineering/Projects/Paseo Passport/paseo-passport" --run-id 20260504T055050436139Z --json
python3 scripts/de.py alerts "/Users/huangquanyong/Projects/ObsidianVault/02 Engineering/Projects/Paseo Passport/paseo-passport" --run-id 20260504T055050436139Z --json
```

## Risks

- Resolution matching could accidentally hide a real blocker. Mitigate by
  requiring a current violation match and keeping both original and resolved
  views visible.
- CLI surface could become too human-facing. Mitigate by keeping command output
  JSON-first and documenting it as Codex-facing.
- Historical terminal runs may still feel unsatisfying. Mitigate by explicitly
  stating that resolution is an audit overlay, not terminal state rewriting.

## Follow-ups

- Coordinator re-entry after decisions or all protocol blockers are resolved.
- A reversal/supersession command for mistaken resolution records.
