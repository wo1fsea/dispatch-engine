---
language: en-US
audience: agent
doc_type: normative
---

# Documentation Standards

Documentation is project surface. It should have a clear source of truth, audience, scope, validation path, and retirement path.

## When Required

Apply this when a change:

- Adds, moves, renames, deletes, or substantially rewrites a doc.
- Changes user/API-visible behavior that existing docs describe.
- Changes commands, configuration, environment variables, file formats, schemas, setup, deployment, validation, or troubleshooting steps.
- Adds or changes examples, snippets, templates, generated docs, screenshots, diagrams, or public contributor guidance.
- Changes agent instructions, governance files, specs, or routing docs such as `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, or `docs/README.md`.

If a behavior change does not require documentation, record why in the PR, workstream, or change note.

## Language And Audience

Every new or substantially changed durable doc must declare its language near the top.

```yaml
---
language: en-US
audience: agent
doc_type: normative
---
```

Rules:

- Use `en-US` for agent-facing docs by default.
- Use the target reader's language for user-facing or team-facing docs.
- Use `mixed` only when multiple languages are intentional, and label sections clearly.
- Do not mix languages casually inside normative instructions.
- Code identifiers, commands, paths, flags, API names, and error strings remain literal.
- Use a hidden comment metadata block when YAML frontmatter would leak into generated output.

Existing docs without metadata should be backfilled when touched, moved, audited, or promoted.

## Required Rules

1. Define one source of truth.
   - Do not copy the same rule, command, API shape, or setup instruction into multiple long-lived docs.
   - If multiple entrypoints need the same information, make one canonical and point the others to it.

2. State audience and scope early.
   - A reader should quickly know whether the doc is for users, contributors, maintainers, operators, reviewers, or agents.

3. Keep routers thin.
   - Entry files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Copilot instructions, root README sections, and docs indexes should route, not duplicate.
   - When adding, deleting, renaming, or moving canonical docs, update the router in the same change.

4. Update docs with behavior.
   - Code changes that alter documented behavior must update the relevant docs in the same change or record why no doc update is needed.

5. Validate examples and commands.
   - Commands should include working directory, required environment, expected output shape, or validation context when not obvious.
   - Snippets and examples must either be runnable/verified or clearly marked illustrative.

6. Treat generated docs as generated.
   - Record the generator or source.
   - Update the source and regenerate instead of hand-editing generated output, unless the repo documents an exception.

7. Delete or supersede stale docs.
   - When a doc is obsolete, remove it or mark it superseded with the replacement path.
   - Do not preserve old docs without owner and review condition.

8. Separate durable docs from working notes.
   - Drafts, raw agent notes, debug output, screenshots, recordings, traces, and generated reports stay in `.out/` until accepted or promoted.

## Documentation Evidence

```markdown
## Documentation Evidence

- Docs updated / N/A:
- Language/audience/doc type declared:
- Source of truth:
- Routers or indexes updated:
- Links checked:
- Examples or commands checked:
- Generated docs regenerated / N/A:
- Stale docs removed or superseded:
```
