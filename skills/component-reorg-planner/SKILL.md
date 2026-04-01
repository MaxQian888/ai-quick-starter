---
name: component-reorg-planner
description: Use when auditing a React or Next.js component directory before reorganizing files into function-based subfolders, especially when Codex must follow the repository's existing structure instead of forcing a generic feature-first rewrite.
---

# Component Reorg Planner

Audit a component directory first. Produce a conservative reorganization plan that groups move-worthy components by function while preserving the repository's current structure signals.

## Workflow

1. Confirm the real repository root and the exact component directory to audit.
2. Detect project context before proposing any subfolders:

```bash
python scripts/detect_component_context.py --root <repo-root> --target <component-dir> --pretty
```

3. Build the reorganization plan:

```bash
python scripts/build_component_reorg_plan.py --root <repo-root> --target <component-dir>
```

4. Read the JSON output first. Use the Markdown report for human review.
5. Treat `keep-put` entries as intentional stop signals, not incomplete work.
6. Execute approved moves in a later implementation pass. This skill does not move files.

## Decision Rules

- Reuse the repository's current layout mode before suggesting any folder plan.
- Suggest functional subfolders only for components with clear naming signals such as `Form`, `Table`, `Dialog`, or `Filter`.
- Keep hooks, barrel files, tests, stories, styles, and low-confidence components in place unless the repository already co-locates them under functional folders.
- If the target directory sits inside a feature or route boundary, keep support paths scoped to that same boundary.
- If confidence is low, prefer a partial plan with explicit non-moves over a full speculative reshuffle.

## What To Review In The Report

- `project_context`: detected framework, router mode, and support-path hints.
- `proposed_subfolders`: the confident functional groups worth considering.
- `move_plan`: per-file recommendation with destination and rationale.
- `blocked_or_keep_put`: files intentionally left untouched.
- `forbidden_moves`: actions that would break the current repository contract.
- `verification_suggestions`: checks to run only after a separate execution pass is approved.

## Guardrails

- Do not move files from this skill alone.
- Do not collapse a mixed repository into a new global structure from one local directory audit.
- Do not create a catch-all `shared` folder just to force movement.
- Do not move barrel files before downstream imports are mapped.
- Do not claim the plan is repo-aligned unless the detected layout signals support it.

## References

- Read [references/layout-detection.md](references/layout-detection.md) for structure detection rules and support-path policy.
- Read [references/grouping-rules.md](references/grouping-rules.md) for functional grouping heuristics and stop conditions.
- Read [references/output-schema.md](references/output-schema.md) for the JSON and Markdown output contract.
