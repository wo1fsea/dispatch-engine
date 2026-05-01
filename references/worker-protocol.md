---
language: en-US
audience: agent
doc_type: normative
---

# Worker Protocol

Use this reference when changing worker or reviewer adapters.

## Worker Input

A worker receives:

- target repository path
- objective
- one workstream
- relevant repository instructions
- allowed file scope when known
- validation expectations

## Worker Output

A worker returns:

- status: `done`, `done_with_concerns`, `needs_context`, `blocked`, or `failed`
- summary
- changed files
- validation run
- questions or blockers

## Rule

Each worker owns one workstream at a time. Parallel workers must be told they are not alone in the codebase and must avoid files outside their declared scope.
