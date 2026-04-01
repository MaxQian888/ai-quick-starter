---
name: component-reorg-executor
description: Use when applying an approved component-reorg-planner JSON report to move React or Next.js components into already-approved functional subfolders while repairing local relative imports and barrel exports without re-planning the structure.
---

# Component Reorg Executor

Execute an approved component reorganization plan exactly as written. Move only the planner-approved files, then repair local relative imports and barrel exports inside the audited directory.

## Workflow

1. Confirm the planner JSON is approved and still matches the current repository state.
2. Run the executor against the planner JSON:

```bash
python scripts/apply_component_reorg_plan.py --plan <path-to-component-reorg-plan.json>
```

3. Read the JSON execution report first. Use the Markdown report for review.
4. Re-run only the narrowest verification that covers the touched directory.
5. If the planner JSON is stale or the working tree no longer matches it, stop and regenerate the plan.

## Execution Rules

- Execute only `action=move` entries from the planner JSON.
- Leave `keep-put` entries where they are.
- Repair target-local relative imports after the move graph is applied.
- Repair barrel exports that point at moved files.
- Keep the rewrite scope inside the planned target directory unless the user explicitly broadens it.

## Guardrails

- Do not re-decide functional buckets in this skill.
- Do not move hooks, tests, stories, styles, or type files unless the planner JSON explicitly marks them as `action=move`.
- Do not widen import rewrites into unrelated packages or applications.
- Do not claim the execution succeeded unless the move graph and scoped verification both ran.
- Do not execute a planner JSON generated for a different repository root.

## What To Review In The Report

- `summary`: moved files, rewritten files, skipped entries
- `applied_moves`: the exact old-to-new path graph
- `rewritten_files`: files whose relative imports or exports changed
- `skipped_entries`: planner entries intentionally left untouched by execution

## References

- Read [references/input-contract.md](references/input-contract.md) for the accepted planner JSON contract.
- Read [references/import-rewrite-policy.md](references/import-rewrite-policy.md) for rewrite scope and stop conditions.
- Read [references/output-schema.md](references/output-schema.md) for the execution report fields.
