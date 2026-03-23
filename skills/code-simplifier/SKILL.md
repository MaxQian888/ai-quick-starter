---
name: code-simplifier
description: Use when recently modified code should be simplified for clarity, consistency, and maintainability without changing behavior, especially after implementation, during focused cleanup requests, or when a diff needs safer naming, control-flow, and structure improvements instead of broader rewrites.
---

# Code Simplifier

## Overview

Refine changed code after implementation, not before understanding it.
Keep behavior, public contracts, and validation intact while making the touched code easier to read, review, and extend.

## Workflow

1. Lock the scope before editing.
- Default to recently modified code only.
- Run `uv run --python 3.11 scripts/detect_refinement_scope.py --repo-root <repo> --json`.
- If the user names files, directories, or a diff, treat that as the hard boundary even if git shows more changes.
- If there is no reliable git signal, stay inside explicitly provided files or the files touched in the current session.

2. Read repository standards before simplifying.
- Check `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, nearby modules, and local lint or format config.
- If the repo has no explicit standard, infer from adjacent files and keep the changes conservative.
- Read [references/standards-discovery.md](references/standards-discovery.md) when standards conflict or are incomplete.

3. Preserve behavior explicitly.
- Keep exported names, props, function signatures, return shapes, side-effect order, async sequencing, error semantics, and user-visible text unchanged unless the user asks otherwise.
- Do not mix simplification with feature work, dependency churn, or repo-wide formatting passes.
- Read [references/preservation-checklist.md](references/preservation-checklist.md) before touching high-risk code.

4. Simplify the right things.
- Flatten needless nesting and reduce control-flow noise.
- Remove redundant temporary variables, dead branches, and one-off abstractions that hide simple logic.
- Split dense expressions into named intermediate steps when that improves readability.
- Align names, imports, and file-local structure with surrounding code.
- Prefer explicit `if/else` chains or `switch` blocks over nested ternaries.
- Prefer readable code over fewer lines.

5. Apply project standards without inventing new ones.
- Use sorted ESM imports with explicit extensions when the repo does.
- Prefer `function` declarations for top-level JavaScript or TypeScript functions when that matches local practice.
- Add explicit return types for top-level functions when the project expects them.
- Use explicit `Props` types for React components when the project already follows that pattern.
- Avoid broad `try/catch` blocks unless the surrounding boundary already depends on them.

6. Verify at the same scope you edited.
- Re-run focused lint, typecheck, test, or build commands that prove behavior did not change.
- If automation is unavailable, state that clearly and do a tight manual reasoning pass over the preserved behavior.

7. Report only meaningful refinements.
- Summarize structural simplifications, standard-alignment decisions, and any remaining risky areas.
- Do not produce a changelog of trivial formatting-only edits.

## Guardrails

- Do not expand from the touched diff into neighboring cleanup unless it is required to keep the code coherent.
- Do not change runtime behavior to satisfy style preferences.
- Do not replace explicit code with clever one-liners.
- Do not introduce nested ternaries.
- Do not rename public APIs without an explicit request.
- Do not simplify by deleting validation, error branches, or edge-case handling that still serves a real path.

## Reference Files

- [references/standards-discovery.md](references/standards-discovery.md): source-of-truth order for project conventions and fallback rules when `CLAUDE.md` is missing.
- [references/preservation-checklist.md](references/preservation-checklist.md): behavior invariants to preserve before and after simplification.

## Helper Script

- [scripts/detect_refinement_scope.py](scripts/detect_refinement_scope.py): inspect git-backed recent changes and emit a focused refinement scope.

Example:

```bash
uv run --python 3.11 scripts/detect_refinement_scope.py --repo-root . --json
```
