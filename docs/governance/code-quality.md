---
language: en-US
audience: agent
doc_type: normative
---

# Code Quality

Use these rules as review gates for code changes. Violations should be fixed or recorded as explicit, owned exceptions.

## Related Gates

- Before adding or expanding project surface, apply `docs/governance/change-gate.md`.
- When producing screenshots, recordings, traces, logs, generated reports, debug dumps, or scratch files, apply `docs/governance/temp-artifacts.md`.

## Required Rules

1. Remove dead code.
   - Delete unused functions, exports, classes, components, routes, flags, configs, unreachable branches, stale adapters, and obsolete compatibility paths.
   - Keep legacy code only when it has an owner, a reason, and a deletion condition.

2. Keep capability interfaces orthogonal.
   - Each public function, API, command, option, or configuration field should represent one independent concept.
   - Do not combine unrelated behavior behind positional flags, mode strings, or overloaded parameters.
   - If parameters constrain each other, introduce a named options object, split the interface, or model the valid states explicitly.

3. Separate commands from queries.
   - Query-shaped APIs must not mutate durable state, create records, emit irreversible side effects, or hide refresh/write behavior.
   - Mutating APIs should be named as commands and document their side effects.

4. Model state explicitly.
   - Do not represent complex lifecycle state with loose boolean clusters.
   - Prefer a single status enum, tagged union, state machine, or domain object that makes invalid states unrepresentable.

5. Keep side effects at boundaries.
   - Core logic should not directly read the network, database, filesystem, environment, current time, randomness, process state, or global mutable state.
   - Pass side-effectful dependencies through parameters, adapters, services, or dependency injection points that are easy to test.

6. Maintain one source of truth.
   - Do not store the same business state in multiple fields, caches, configs, or services without a documented owner.
   - If denormalization or caching is required, define invalidation, precedence, and conflict resolution.

7. Collapse duplicate business rules.
   - When the same business rule appears a third time, centralize it or record why duplication is safer for now.

8. Reject speculative abstractions.
   - Do not add frameworks, base classes, plugin systems, generic engines, or extension points for hypothetical future use.
   - Abstract from real repetition, separate ownership, or proven variation.

9. Name code by its real behavior.
   - Function and module names must expose meaningful side effects.
   - `validateUser` must not write records. `formatConfig` must not read environment.

10. Design lifecycle APIs as a set.
    - If a capability has `create`, decide whether `update`, `delete`, `archive`, `restore`, `list`, and `get` exist.
    - If an operation is intentionally absent, record the product or domain reason.

11. Use distinguishable errors.
    - Callers should be able to distinguish validation, permission, not-found, conflict, timeout, dependency failure, and internal failure when those cases require different handling.

12. Govern dependencies.
    - New dependencies need a reason, an owner, and a note on why the standard library or existing dependency is not enough.

13. Govern TODOs and incomplete code.
    - `TODO`, `FIXME`, temporary flags, and partial compatibility paths must include an owner or issue/spec id.

14. Govern configuration and feature flags.
    - Every config or flag needs a default, scope, owner, and removal or review condition.
    - Expired flags and unused config are dead code.

15. Give compatibility layers an exit plan.
    - Migration paths, adapters, legacy branches, fallbacks, and shims must state why they exist and when they can be deleted.

## Exception Format

```markdown
## Code Quality Exception

- Rule:
- Reason:
- Owner:
- Remove or revisit when:
- Tracking issue/spec:
- Validation:
```
