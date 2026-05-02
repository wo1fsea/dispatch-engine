---
workstream_id: 01-decision-guidance
language: en-US
audience: agent
doc_type: workstream
status: completed
owner: codex-worker
branch: main
updated: 2026-05-02
depends_on:
  - rfc-0008
---

# Decision Guidance

Document when coordinators should stop and request operator decisions.

## Result

Added `references/decision-blocker-protocol.md` and `references/prompts/decision-blocker-guidance.md`.

The guidance keeps decision judgment skill-first:

- Coordinators ask rather than guess on scope, risk, conflicts, validation ambiguity, dependency conflicts, or existing parallel changes.
- Workers stop and report blockers instead of silently broadening assigned scope.
- Reviewers and validators treat unresolved blockers as state signals, not product decisions.
- Interactive Codex/operator remains the decision maker.
