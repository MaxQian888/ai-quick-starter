---
name: split-commit-fixer
description: |
  Use whenever a git worktree has large uncommitted changes that need to be split into reviewable commit batches. Also trigger when the user wants to group changes by feature, fix commit-time lint/test/type-check failures incrementally, or consolidate multiple checkpoint commits into a smaller final history. Make sure to use this skill whenever the user says "split commits", "organize commits", "commit batches", "checkpoint commits", "squash", "rebase", "clean history", or "my changes are too big for one commit" — even for medium-sized changes that just need better grouping. Also trigger before creating a pull request when the working tree has mixed concerns. Covers Conventional Commits, quality-gate driven commits, and safe checkpoint-then-squash workflows.
---

# Split Commit Fixer

Plan commit-sized batches before staging anything. Keep coupled files together, commit one batch at a time, fix quality-gate failures as they surface, then automatically collapse the checkpoint commits into clean final history.

## Adaptive Detection

Before splitting, detect the repository state:

1. **Git status**: Confirm this is a git worktree with uncommitted changes.
2. **Change scope**: Estimate file count and concern mixing from `git status`.
3. **Quality gates**: Identify lint, test, typecheck, and build commands from manifests and CI.
4. **Commit style**: Check if the project uses Conventional Commits or another commit convention.
5. **Consolidation preference**: Ask if the user wants final, scoped, or checkpoint history.

Use these signals to tune batch grouping and quality-gate selection.

## Workflow

1. Confirm you're inside a git worktree and inspect the dirty state.
2. Run the helper script to get a deterministic plan:

   ```bash
   uv run --python 3.11 scripts/plan_commit_batches.py --project-root <repo> --json
   ```

3. Review the output fields: `quality_gate_commands`, `batches`, `recommended_order`, `post_commit_consolidation`, and `global_cautions`.
4. Record the pre-split checkpoint from `post_commit_consolidation.checkpoint` before the first temporary batch commit.
5. Pick the first batch and stage only its files or hunks.
6. Start with the batch's `quality_gate_plan.narrow_commands`, then expand to `quality_gate_plan.full_commands` once the local failure is fixed.
7. Fix the first real blocker with the smallest valid change.
8. Re-run the failing check, then re-run the broader gate chain for that batch.
9. Write a Conventional Commit message from the batch intent, not from the entire worktree. Treat each batch commit as a temporary checkpoint.
10. Commit the batch, then rebuild the plan before committing the next one.
11. After all planned batches commit cleanly, run the consolidation `verification_commands`.
12. Choose how to collapse the checkpoint commits:
    - **final** (default): squash everything into one commit.
    - **scoped**: one commit per consolidation group.
    - **checkpoint**: keep the temporary commits as final history.
13. If the verification checks pass, execute the selected plan. `post_commit_consolidation.execution_steps` mirrors the **final** granularity.
14. If a consolidation check fails, stop and keep the checkpoint commits.

## Batch Rules

- Split by feature, subsystem, or clearly independent concern.
- Keep matching tests and docs with the same feature when they describe or verify it.
- Attach root config, lockfiles, and shared tooling only when one feature clearly owns them.
- Stop splitting when a file is partially staged, renamed across concerns, or shared by multiple features.
- Prefer one coherent commit over several fragile ones.

## Repair Loop

1. Stage the selected batch.
2. Run the smallest repository-native gate that matches the current failure.
3. Fix the root cause inside the current batch boundary.
4. Re-run the same failing gate.
5. Re-run the main gate chain for the batch.
6. Commit only after the gates pass or the remaining blocker is clearly environmental.
7. Do not run the final squash while any batch remains blocked.

If the same gate fails after three focused attempts, stop and report the failing command, the attempted fixes, and why the batch is still blocked.

## Guardrails

- Do not force unrelated files into a batch just to make one commit pass.
- Do not use `git commit --no-verify` unless the user explicitly asks for it.
- Do not split lockfiles, root manifests, or shared config across multiple commits without evidence that they are independent.
- Do not present a batch plan from a non-git directory as if it were safe to commit.
- Rebuild the batch plan after each commit; the remaining worktree is new evidence.
- Do not squash across commits that predate the recorded base checkpoint.
- Do not run the final squash while the worktree is dirty or the completed-batch count no longer matches the plan.
- If a consolidation safety check fails, keep the checkpoint commits instead of forcing a squash.
- Do not claim a finer-grained history exists unless it matches one of the generated consolidation groups.

## Example

```bash
uv run --python 3.11 scripts/plan_commit_batches.py --project-root . --json
```

The script accepts only `--project-root` and `--json`. Re-run it after each commit so the next plan reflects the remaining worktree.

## References

- `references/commit-splitting.md` — grouping heuristics, coupling warnings, commit sequencing, and consolidation safety rules.
- `references/linked-skills.md` — when to chain into `commit-quality-fixer`, `build-project-fixer`, or `github-actions-ci-builder`.

## Reading the Plan JSON

Each batch carries a `quality_gate_plan` with three fields:

- `narrow_commands`: smallest checks to run first.
- `full_commands`: full chain to re-run before committing.
- `repair_loop`: ordered repair guidance generated for that batch's kind. Prefer this over reinventing a generic loop, since it adapts to docs, test, config, and feature batches differently.

The top-level `post_commit_consolidation` block holds the default squash plan, the available granularity levels, the scope-level consolidation groups, the required safety checks, and the fallback rule that keeps checkpoint commits when any safety check fails. Read it before the first batch commit so the final squash is deterministic.
