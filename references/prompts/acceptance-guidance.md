---
language: en-US
audience: agent
doc_type: prompt-guidance
---

# Acceptance Guidance Prompt Addendum

Use this addendum with coordinator, reviewer, and validator prompts when a
workstream acceptance call is needed.

- Combine worker reports, reviewer reviews, validator validation, and
  decision/blocker records before recommending a workstream state.
- Treat `accepted` as a coordinator/operator conclusion over combined evidence,
  not as the automatic result of one passing report.
- Use `changes_requested` or `needs-fix` when scoped implementation work remains
  and the path forward is clear.
- Use `blocked` when the next step requires a decision, scope expansion,
  dependency override, shared-file ownership call, or acceptance of residual
  risk.
- Use `failed` only when the workstream path is not viable in the current run
  without replanning.
- Record the exact evidence path you relied on: worker report path, review path,
  validation path, decision id, or blocker id.
- Do not invent scheduler behavior or silently broaden scope to reach
  acceptance.
