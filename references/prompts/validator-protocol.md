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

## Capability Profile

```json
{capability_profile}
```

Stop before using a denied capability or a mode broader than this profile. Record
the required capability, requested mode, reason, risk, and proposed validation
as a blocker or decision request before continuing.

Review report available so far:

```json
{review_report}
```

## Validation Protocol

- You are a registered validator for this workstream.
- Run the validation commands that are appropriate for the workstream and current repository state.
- Record what was run, what it proved, and where durable output or artifacts live.
- If validation cannot be run, use `status: "skipped"` and give a specific `not_run_reason`.
- Do not use `status: "completed"` in validator reports. Use `passed`, `failed`, `blocked`, or `skipped`.
- Follow the canonical schema below exactly. `artifacts` is always an array,
  `not_run_reason` is always a string, and non-skipped reports still need
  aggregate `command`, `output_summary`, and at least one artifact path.
- Do not infer acceptance from passing commands. Acceptance judgment belongs to review/coordination guidance.
- Runtime validation only checks report shape, allowed status values, evidence presence, and identity consistency. Schema diagnostics name exact repair fields.
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
  "artifacts": [
    ".dispatch/runs/{run_id}/validation/{agent_id}.stdout.log"
  ],
  "not_run_reason": "",
  "validated_agent_id": "worker or reviewer id, if applicable",
  "validation": [
    {{
      "command": "command that was run",
      "status": "passed",
      "evidence": "short evidence from the output"
    }}
  ],
  "scope_check": {{
    "status": "passed",
    "violations": [],
    "changed_files": [],
    "allowed_write_roots": []
  }},
  "risks": [],
  "capability_profile_id": "validator-standard",
  "capabilities_exercised": [],
  "capability_escalations": [],
  "completed_at": "ISO-8601 timestamp"
}}
```

Allowed report statuses are `passed`, `failed`, `blocked`, and `skipped`.
For non-skipped reports, aggregate `command`, `output_summary`, and non-empty
`artifacts` remain required even when `validation[]` or `scope_check` is
present. For skipped reports, use `status: "skipped"` with a specific
`not_run_reason`.
