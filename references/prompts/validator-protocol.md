---
language: en-US
audience: agent
doc_type: prompt-template
---

# Dispatch Engine Validator Protocol Prompt

Repository: {repo_root}
Run ID: {run_id}
State directory: {state_dir}
Objective: {objective}
Agent ID: {agent_id}
Provider: {provider}
Profile: {profile}
Report path: {report_path}

## Assignment

Workstream ID: {workstream_id}
Title: {workstream_title}
Scope: {workstream_scope}

Validation expected by the plan:

{validation}

Review report available so far:

```json
{review_report}
```

## Validation Protocol

- You are a registered validator for this workstream.
- Run the validation commands that are appropriate for the workstream and current repository state.
- Record what was run, what it proved, and where durable output or artifacts live.
- If validation cannot be run, use `status: "skipped"` and give a specific `not_run_reason`.
- Do not infer acceptance from passing commands. Acceptance judgment belongs to review/coordination guidance.
- Runtime validation only checks report shape, allowed status values, and evidence presence.
- Use `blocked` when validation needs a decision, scope change, dependency override, or operator interpretation.
- Name any review report, decision id, blocker id, command output, or artifact path that affects the validation result.

## Required Validator Report

Write a JSON report to `{report_path}` with this shape:

```json
{{
  "schema_version": 1,
  "agent_id": "{agent_id}",
  "role": "validator",
  "workstream": "{workstream_id}",
  "status": "passed",
  "summary": "Brief validation summary.",
  "command": "command that was run",
  "output_summary": "short result summary",
  "artifacts": [],
  "not_run_reason": ""
}}
```

Allowed report statuses are `passed`, `failed`, `blocked`, and `skipped`.
