---
workstream_id: 02-fake-provider-fixture
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: dispatch-engine
branch: main
updated: 2026-05-02
depends_on:
  - 01-runbook-and-plan-fixture
---

# Fake Provider Fixture

Covered by `tests/test_dogfood_runbook_fixture.py`, which puts a deterministic
fake `codex` executable on `PATH` and exercises live-form coordinator state
without calling a real provider.
