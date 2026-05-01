---
language: en-US
audience: agent
doc_type: normative
---

# Validation Workflow

## Rule

Do not skip validation silently.

For UI-visible changes, visual evidence is required unless explicitly marked not applicable.

## Validation Ladder

1. Static checks or formatting.
2. Narrow unit tests.
3. Relevant integration tests.
4. End-to-end or manual checks for user-facing flows.
5. Screenshots, recordings, logs, or traces when they are the clearest proof.

## UI / Visual Evidence

Use this gate when a change affects rendering, layout, spacing, sizing, typography, color, imagery, responsive behavior, user-visible copy, interaction flows, visual states, canvas, Three.js, charts, maps, or animation.

Default evidence:

- At least one screenshot or short recording of the changed flow.
- Relevant states chosen by risk: normal, loading, empty, error, disabled, hover, focus, selected, expanded, collapsed, or success.
- Desktop viewport for most changes.
- Mobile viewport when layout, responsive behavior, touch interaction, or narrow-screen content may be affected.

If visual evidence is not applicable, record why and provide substitute evidence.

Store screenshots, recordings, traces, and other validation artifacts according to `docs/governance/temp-artifacts.md`.

## Reporting

Record:

- Commands run.
- Manual checks performed.
- Visual evidence or why it is not applicable.
- Tests not run and why.
- Residual risk.
