---
language: en-US
audience: agent
doc_type: router
---

# Specs

Use `docs/governance/spec-production.md` for creating specs, `docs/governance/spec-workflow.md` for the spec lifecycle, `docs/governance/spec-id-policy.md` for id format, `docs/governance/spec-execution-status.md` for execution status, and `docs/governance/multi-agent-spec-flow.md` for parallel implementation.

Each substantial spec should live under:

```text
specs/<source>-<id>-<short-slug>/
  PRODUCT.md
  TECH.md
  STATUS.md
  workstreams/
    01-implementation.md
```

## Current Specs

- `rfc-0001-initial-governance`: initial repository governance.
- `rfc-0002-skill-first-packaging`: root-level runtime-backed skill packaging.
