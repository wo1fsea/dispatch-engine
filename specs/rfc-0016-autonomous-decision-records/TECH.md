---
spec_id: rfc-0016-autonomous-decision-records
language: en-US
audience: agent
doc_type: spec
status: planned
created: 2026-05-03
---

# Autonomous Decision Records Tech Spec

## Boundary

Autonomous technical choice eligibility remains a skill/heartbeat responsibility.
The runtime only accepts a structured assertion from interactive Codex, validates
the minimum mechanical invariants, records it durably, emits the normal
`decision.resolved` event, and surfaces the record in status.

## Decision Record Shape

Resolved autonomous records extend the latest decision entry:

```json
{
  "schema_version": 1,
  "decision_id": "decision-001",
  "id": "decision-001",
  "status": "resolved",
  "question": "Choose internal adapter shape.",
  "selected_option_id": "minimal_adapter",
  "resolution": "Autonomous technical choice after 4 unanswered heartbeat checks.",
  "resolved_by": "interactive-codex-autonomous",
  "resolved_at": "2026-05-03T00:00:00Z",
  "resolution_mode": "autonomous_technical",
  "autonomous_decision": {
    "trigger": "four_unanswered_heartbeats",
    "unanswered_heartbeat_count": 4,
    "heartbeat_interval_minutes": 15,
    "first_seen_heartbeat_id": "heartbeat-000012",
    "last_seen_heartbeat_id": "heartbeat-000015",
    "technical_scope": true,
    "conservative": true,
    "reversible": true,
    "inside_approved_objective": true,
    "excluded_categories": [
      "product_behavior",
      "security_privacy",
      "deployment",
      "credentials",
      "destructive_data",
      "legal_financial",
      "business_scope"
    ],
    "rationale": "Minimal adapter keeps existing contracts and can be replaced later.",
    "validation_expected": [
      "PYTHONPATH=scripts python3 -m unittest discover -s tests"
    ]
  }
}
```

## Runtime Validation

For `resolution_mode == "autonomous_technical"`:

- `actor` must be `interactive-codex-autonomous`.
- `autonomous_decision.trigger` must be `four_unanswered_heartbeats`.
- `unanswered_heartbeat_count` must be at least `4`.
- `heartbeat_interval_minutes` must be a positive integer and defaults to `15`.
- `technical_scope`, `conservative`, `reversible`, and
  `inside_approved_objective` must all be `true`.
- `rationale` must be non-empty.
- `excluded_categories` must include the standard non-autonomous categories.
- `validation_expected` must be a non-empty list of validation command strings.

The runtime must not inspect code or infer whether the selected option is truly
technical. That remains a review responsibility.

## CLI Contract

Extend `resolve-decision` with Codex-facing flags:

```bash
--autonomous-technical
--unanswered-heartbeats <count>
--heartbeat-interval-minutes <minutes>
--first-seen-heartbeat-id <id>
--last-seen-heartbeat-id <id>
--autonomous-rationale <text>
--validation-expected <command>  # repeatable
--excluded-category <category>  # repeatable; defaults to standard exclusions
```

When `--autonomous-technical` is present, `--actor` defaults to
`interactive-codex-autonomous`. Explicit actor overrides should be rejected
unless they match the same value.

## Status Contract

`status --json` should include:

```json
{
  "autonomous_decisions": {
    "count": 1,
    "records": [
      {
        "decision_id": "decision-001",
        "selected_option_id": "minimal_adapter",
        "resolved_at": "2026-05-03T00:00:00Z",
        "rationale": "Minimal adapter keeps existing contracts and can be replaced later.",
        "validation_expected": [
          "PYTHONPATH=scripts python3 -m unittest discover -s tests"
        ]
      }
    ]
  }
}
```

Keep full source-of-truth records in `decisions.jsonl`; status is a convenience
view for interactive Codex final reporting.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_autonomous_decision_records
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py resolve-decision --help
python3 scripts/de.py status --help
git diff --check
```
