---
language: en-US
audience: agent
doc_type: normative
---

# Spec ID Policy

## Format

Use:

```text
specs/<source>-<id>-<short-slug>/
```

Examples:

```text
specs/gh-123-open-file-tilde/
specs/linear-app-1066-agent-autonomy/
specs/jira-core-42-auth-retry/
specs/rfc-0001-repo-governance/
specs/adhoc-20260430-tdd-bootstrap/
```

## Rules

- Use lowercase kebab-case.
- Use `gh-<number>-<slug>` for GitHub issues.
- Use `linear-<team>-<number>-<slug>` for Linear tickets.
- Use `jira-<project>-<number>-<slug>` for Jira tickets.
- Use `rfc-<4-digit-number>-<slug>` for governance, architecture, or process decisions.
- Use `adhoc-<YYYYMMDD>-<slug>` only for short-lived exploration.
- Treat the source id as stable and the slug as human-readable context.
