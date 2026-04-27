---
name: component-reorg-executor
description: >
  Make sure to use this skill whenever the user wants to execute an approved
  component reorganization plan, move React or Next.js components into new
  subfolders, apply a planner JSON report, or reorganize a component directory
  after planning. Also trigger for "move these components," "apply the reorg
  plan," "execute component moves," "restructure my components folder," or
  "implement the approved component layout." Covers synonyms like "component
  reorganization," "folder restructuring," "apply migration plan," "execute
  moves," and "component directory cleanup." Use it only when a planner JSON
  already exists or the user explicitly approves the move plan.
---

# Component Reorg Executor

Execute an approved component reorganization plan exactly as written. Move only the planner-approved files, then repair local relative imports and barrel exports inside the audited directory.

## Adaptive Detection

Before executing, verify the execution context:

- Confirm the planner JSON exists and is approved by the user.
- Check that the planner JSON matches the current repository state (no stale paths).
- Detect the framework: React, Next.js, or other.
- Identify the target directory scope; do not widen beyond the planned boundary.
- Check for barrel files (`index.ts`, `index.js`) that may need export rewrites.

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

## Examples

**Execute an approved plan:**
```bash
python scripts/apply_component_reorg_plan.py --plan ./plans/component-reorg-plan.json
```

**Execute with custom project root:**
```bash
python scripts/apply_component_reorg_plan.py --plan ./plans/reorg.json --root ./my-app
```

## References

- Read [references/input-contract.md](references/input-contract.md) for the accepted planner JSON contract.
- Read [references/import-rewrite-policy.md](references/import-rewrite-policy.md) for rewrite scope and stop conditions.
- Read [references/output-schema.md](references/output-schema.md) for the execution report fields.
