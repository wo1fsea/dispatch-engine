---
language: en-US
audience: agent
doc_type: spec
---

# Codex Heartbeat Observation Tech Spec

## Design Boundary

Dispatch Engine has three cooperating layers:

1. **Interactive Codex layer**: talks to the user, reads target repo rules,
   prepares explicit dispatch plans, starts runs, interprets status, asks for
   decisions, and performs final review.
2. **Dispatch Engine runtime layer**: imports plans, launches foreground or
   detached provider coordinators, records `.dispatch/` state, exposes
   scriptable status/event/decision surfaces, and performs mechanical protocol
   checks.
3. **Host wakeup layer**: wakes the current Codex thread on a schedule when
   supported. In the Codex desktop app this can be a thread heartbeat
   automation. This layer is outside Dispatch Engine.

The runtime must not pretend it can wake a chat thread. It can only write state
that a woken or user-prompted Codex can read.

## Codex-Facing CLI Contract

CLI additions should be designed for Codex tool use first:

- Prefer `--json` as the stable contract.
- Use deterministic ids, enum-like action types, and absolute or repo-relative
  state paths.
- Keep human-readable output as a debugging convenience only.
- Do not require interactive prompts, pagers, cursor UIs, or terminal state.

Near-term command surfaces:

```bash
python3 scripts/de.py status <repo> --json
python3 scripts/de.py events <repo> --since <event-id> --json
python3 scripts/de.py alerts <repo> --json
python3 scripts/de.py resolve-decision <repo> --id <decision-id> --option <option-id> --json
```

`status --json` is the primary summary surface and should grow a
`next_actions` array for Codex:

```json
{
  "next_actions": [
    {
      "type": "decision_required",
      "decision_id": "decision-001",
      "recommended_option": "approve_scope_expansion"
    },
    {
      "type": "repair_report_schema",
      "agent_id": "reviewer-001"
    }
  ]
}
```

`events --since` and `alerts --json` are mechanical helpers that let a woken
Codex distinguish material changes from unchanged background activity.

## Heartbeat Prompt Contract

When the Codex host supports a thread heartbeat, interactive Codex should create
or suggest one after `de run --detach` for long-running work. The heartbeat task
should:

1. Read the target repo path and Dispatch Engine skill path from the prompt.
2. Run `de status <repo> --json`.
3. Optionally run `de events <repo> --since <last-seen-event-id> --json` once
   event delta support exists.
4. Report only material changes: completed workstreams, blocked workstreams,
   failed agents, pending decisions, new protocol violations, run completion,
   or validation evidence.
5. Ask for user input only when a pending decision or unrecoverable blocker is
   present.
6. Avoid claiming live progress from chat memory alone.

If no heartbeat is configured or supported, the skill should state that Codex
will check the latest `.dispatch/` state when the user next asks.

## Runtime Snapshot Direction

Future runtime work may add current-state snapshots under `.dispatch/current/`:

```text
.dispatch/current/status.json
.dispatch/current/summary.md
.dispatch/current/alerts.jsonl
```

These files are convenience views over `.dispatch/runs/<run-id>/` state. They
must not become a second source of truth.

## Workstreams

1. **Spec and guidance baseline**: update spec, skill, operator flow, and notes
   to record the heartbeat observation boundary.
2. **Codex-facing control surface**: add machine-readable decision resolution,
   event delta, alert, and next-action surfaces.
3. **Host heartbeat runbook**: document the prompt shape interactive Codex
   should use when creating a thread heartbeat monitor.
4. **Validation and dogfood**: verify with a detached target run that a heartbeat
   or user-triggered check can summarize new `.dispatch/` changes.

## Validation

For this spec baseline:

```bash
python3 scripts/de.py --help
python3 scripts/de.py status --help
git diff --check
```

For later implementation work:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py events --help
python3 scripts/de.py alerts --help
python3 scripts/de.py resolve-decision --help
git diff --check
```
