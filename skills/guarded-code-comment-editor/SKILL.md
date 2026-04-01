---
name: guarded-code-comment-editor
description: Use when Codex needs to add missing code comments or rewrite machine-sounding comments inside existing source files while preserving the repository's local comment density, terminology, docstring shape, and language-specific style. Trigger for requests to make comments sound human, clean up AI comments, annotate non-obvious logic, or improve comments in mixed-language repositories without turning the code into tutorial prose.
---

# Guarded Code Comment Editor

Edit comments conservatively. Sample the local style first, then add, rewrite, or delete comments so the result reads like it belongs in the repository instead of sounding templated or tutorial-heavy.

## Workflow

1. Confirm the repository root and the target file or directory that may be edited.
2. Run `uv run --python 3.11 scripts/audit_comment_surface.py --root <repo-root> --target <target> --json`.
3. Read `selected_style`, `style_exemplars`, `file_findings`, `safe_edit_hints`, and `forbidden_actions` before touching code.
4. Open representative same-language files from the target area before editing sparse or mixed-style files.
5. Add comments only where intent, edge cases, invariants, or hazards are not obvious from the code.
6. Rewrite or remove comments that narrate the code, repeat template phrasing, or sound like generic AI filler.
7. Keep the local language, punctuation, docstring form, and comment density unless the user explicitly asks for a broader rewrite.
8. Re-check changed files for over-commenting, stale wording, and accidental code edits.
9. Run the narrowest available verification for the touched files or package, then report what was and was not verified.

## Editing Rules

- Prefer explaining why, boundary conditions, or trade-offs over explaining what each line does.
- Reuse nearby terminology. Do not flatten repository-specific words into generic verbs like `handle`, `process`, or `do`.
- If the target area is sparse, keep it sparse. Fix obvious weak comments and add only the missing ones that earn their place.
- If one language in the repo favors docstrings and another favors inline comments, preserve that split.
- Delete comments that became redundant once a better nearby comment already covers the same point.
- Do not change executable code while doing comment-only cleanup unless the user also asked for a code fix.

## Comment Density Rules

- `sparse`: add only the highest-signal comments and remove weak filler.
- `moderate`: match the local density and placement pattern.
- `dense` or `docstring-heavy`: preserve the shape, but compress generic wording and repeated narration.

## References

- Read `references/style-sampling.md` before deciding how much to edit.
- Read `references/human-comment-rules.md` before adding, rewriting, or deleting comments.
- Read `references/language-patterns.md` before touching TypeScript, Python, Shell, or PowerShell comments.

## Helper Script

Run:

```bash
uv run --python 3.11 scripts/audit_comment_surface.py --root <repo-root> --target <target> --json
```

Use the audit as evidence. It should tell you which language dominates, which files are worth imitating, where suspicious comments already exist, and whether the local area should stay minimal.
