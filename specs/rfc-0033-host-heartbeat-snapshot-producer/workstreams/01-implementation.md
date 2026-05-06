---
workstream_id: 01-implementation
language: en-US
audience: agent
doc_type: workstream
status: ready
owner:
branch:
pr:
files:
  - scripts/dispatch_engine/cli.py
  - scripts/dispatch_engine/dashboard.py
  - dashboard/app.js
  - references/heartbeat-observation.md
  - references/operator-flow.md
  - references/operator-guide.md
  - SKILL.md
  - tests/test_dashboard_observer.py
  - tests/test_codex_facing_control_surface.py
  - specs/rfc-0033-host-heartbeat-snapshot-producer/
depends_on: []
updated: 2026-05-06
---

# Workstream 01: Host Heartbeat Snapshot Producer

Add the Codex-facing snapshot writer and update heartbeat guidance so the
dashboard has live host heartbeat state during detached runs.

Validation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
python3 scripts/de.py record-host-heartbeat --help
git diff --check
```
