---
language: en-US
audience: agent
doc_type: normative
---

# Review Workflow

## Before Review

- Link the relevant spec when one exists.
- Summarize behavior changes and implementation shape.
- Check `docs/governance/change-gate.md` when adding or expanding project surface.
- Check `docs/governance/code-quality.md` for structural code-quality issues.
- Check `docs/governance/documentation-standards.md` when docs, examples, generated docs, specs, contributor guidance, or agent instructions changed.
- Check `docs/governance/temp-artifacts.md` when temporary outputs were produced.
- Include validation evidence.
- Call out risks, migrations, and follow-ups.

## PR Template Expectations

Use `.github/pull_request_template.md` when present.

If the template is missing, include at least: summary, spec link, validation, and risk.
