---
language: en-US
audience: agent
doc_type: normative
---

# Event Protocol

Use this reference when changing Dispatch Engine run-state or event-log behavior.

## Initial File Shape

```text
.dispatch/
  runs/
    <run-id>/
      run.json
      events.jsonl
```

## Event Shape

```json
{
  "ts": "20260501T120000Z",
  "type": "plan.created",
  "actor": "dispatch-engine",
  "workstream": "01-implementation",
  "payload": {}
}
```

Events are append-only. Correct mistakes with new events instead of rewriting history unless the run is explicitly discarded.
