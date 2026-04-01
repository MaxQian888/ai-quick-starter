---
name: split-commit-fixer
description: Use when a repository has a large dirty git worktree and Codex must split uncommitted changes into reviewable commit batches by feature or concern, preserve risky couplings, stage and commit each batch in sequence, and fix commit-time lint, test, or type-check blockers without collapsing everything into one commit.
---

# Split Commit Fixer

Plan commit-sized batches before staging anything. Keep coupled files together, commit one batch at a time, and repair the first quality-gate failure inside the current batch before moving to the next.

## Workflow

1. Confirm the current directory is a git worktree and inspect the dirty state.
2. Run `uv run --python 3.11 scripts/plan_commit_batches.py --project-root <repo> --json`.
3. Review `quality_gate_commands`, `batches`, `recommended_order`, and `global_cautions`.
4. Pick the first batch and stage only that batch's files or hunks.
5. Start from the batch's `quality_gate_plan.narrow_commands`, then widen to `quality_gate_plan.full_commands`.
6. Fix the first real blocker with the smallest valid change.
7. Re-run the failing check, then re-run the broader gate chain for that batch.
8. Write a Conventional Commit message from the batch intent, not from the entire worktree.
9. Commit the batch, then rebuild the plan before committing the next batch.

## Batch Rules

- Split by feature, subsystem, or clearly independent concern.
- Keep matching tests and docs with the feature when they describe or verify the same scope.
- Keep root config, lockfiles, and shared tooling files attached only when one feature clearly owns them.
- Stop splitting when a file is partially staged, renamed across concerns, or obviously shared by multiple features.
- Prefer one coherent commit over multiple fragile commits.

## Repair Loop

1. Stage the selected batch.
2. Run the smallest repository-native gate that matches the current failure.
3. Fix the root cause inside the current batch boundary.
4. Re-run the same failing gate.
5. Re-run the main gate chain for the batch.
6. Commit only after the gates pass or the remaining blocker is clearly environmental.

If the same gate fails repeatedly after three focused attempts, stop and report the failing command, attempted fixes, and why the batch remains blocked.

## Guardrails

- Never force unrelated files into a batch just to make one commit pass.
- Never use `git commit --no-verify` unless the user explicitly asks.
- Never split lockfiles, root manifests, or shared config across multiple commits without evidence that they are independent.
- Never present a batch plan from a non-git directory as if it were safe to commit.
- Rebuild the batch plan after each commit; the remaining worktree may regroup differently.

## References

- Read `references/commit-splitting.md` for grouping heuristics, coupling warnings, and commit sequencing rules.
- Use `scripts/plan_commit_batches.py` to produce a deterministic starting plan before staging.
- Read each batch's `quality_gate_plan` before deciding which command to run first.

## Helper Script

Run:

```bash
uv run --python 3.11 scripts/plan_commit_batches.py --project-root <repo> --json
```

Use the JSON output as a planning artifact. Each batch now includes a `quality_gate_plan` with the smallest suggested checks to run first and the broader command chain to re-run before committing.
