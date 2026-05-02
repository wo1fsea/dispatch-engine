---
language: en-US
audience: agent
doc_type: spec
---

# Detached Coordinator Supervisor Tech Spec

## Proposed Changes

- Add `scripts/dispatch_engine/supervisor.py`.
- Add `de run --detach`.
- Add `supervisors/` to run-state directories.
- Spawn a background supervisor process that calls the existing foreground
  `launch_run_coordinator` path.
- Record supervisor stdout/stderr separately from provider stdout/stderr.
- Expose supervisors through `run_status`.
- Update README, SKILL, operator guide, operator flow, and event protocol.

## Runtime Shape

```text
interactive Codex -> de run --detach -> supervisor process -> foreground provider coordinator
                  <- immediate payload     -> .dispatch state/logs/events
```

The detached supervisor is intentionally small. It is not a daemon and does not
schedule work. It exists only to keep the operator session responsive while the
provider coordinator runs.

## State Files

```text
.dispatch/runs/<run-id>/supervisors/coordinator-001.json
.dispatch/runs/<run-id>/logs/coordinator-001.supervisor.stdout.log
.dispatch/runs/<run-id>/logs/coordinator-001.supervisor.stderr.log
```

## Validation

```bash
PYTHONPATH=scripts python3 -W error::ResourceWarning -m unittest tests.test_detached_coordinator_supervision
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py run --help
git diff --check
```
