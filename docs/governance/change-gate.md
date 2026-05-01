---
language: en-US
audience: agent
doc_type: normative
---

# Change Gate

Use this gate before adding or expanding project surface. Every new surface must prove that it deserves to exist.

## What Counts As Surface

- API endpoint or route.
- Public or exported function, class, component, package export, or module.
- CLI command, option, flag, or output format.
- Configuration field, environment variable, feature flag, or runtime mode.
- Dependency, adapter, integration, provider, or compatibility shim.
- File format, schema, database shape, event format, or protocol message.
- Workflow document, governance file, template, agent entrypoint, or generated starter file.
- Plugin extension point, hook, callback, or user-facing customization point.

## When Required

Run the gate when a change adds, expands, renames, replaces, deprecates, or removes surface.

## Gate Questions

```markdown
## Change Gate

- Problem:
- Existing path considered:
- Why existing path is insufficient:
- Smallest new surface:
- What will be deleted or replaced:
- Owner:
- Validation:
- Temporary or permanent:
- Removal condition:
```

## Rules

- Prefer reuse before adding surface.
- Keep new surface minimal.
- Delete superseded paths in the same change unless compatibility requires retention.
- New configs, flags, adapters, dependencies, workflows, and templates need owners.
- New surface needs validation tied to the surface.
- Temporary surface needs a concrete removal condition.
- Public surface needs compatibility notes.
- Documentation surface counts.
- Dependencies count.

## Compatibility Exception

```markdown
## Compatibility Exception

- Old path:
- New path:
- Why retained:
- Owner:
- Remove when:
- Tracking issue/spec:
- Validation:
```
