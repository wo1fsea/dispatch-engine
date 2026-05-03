---
language: en-US
audience: agent
doc_type: prompt-guidance
---

# Decision Blocker Guidance

Use `references/decision-blocker-protocol.md` when a run reaches a decision,
blocker, or scope-change point.

## Coordinator Prompt Guidance

- Ask instead of guessing when scope, risk, conflicting instructions, validation
  ambiguity, or existing parallel changes require operator judgment.
- Record decision requests with a clear question, reason, and workstream when
  the work can continue after an answer.
- Record blockers when a workstream cannot proceed safely until the issue is
  resolved.
- Resolve decision and blocker records only after the operator or interactive
  Codex has made the choice explicit. Interactive Codex may also make a
  conservative autonomous technical choice after four unanswered heartbeat
  checks, using `resolve-decision --autonomous-technical` so the runtime records
  actor `interactive-codex-autonomous` plus structured metadata; coordinators
  should not invent that fallback themselves.
- Keep runtime use mechanical: append/query records under `.dispatch/`, inspect
  unresolved blockers, and expose status.

## Worker Prompt Guidance

- Stay inside assigned files and accepted scope.
- If the task needs broader scope, stop and report the requested change as a
  blocker instead of silently expanding.
- If another worker's change affects the task, describe the conflict and ask the
  coordinator for a decision.
- Include any blocker id in the worker report so reviewers can connect the
  paused work to durable state.

## Reviewer / Validator Prompt Guidance

- Treat unresolved blockers as a run state signal.
- Do not turn product judgment into a mechanical pass/fail result.
- Ask for a decision when acceptance requires choosing between valid tradeoffs.
