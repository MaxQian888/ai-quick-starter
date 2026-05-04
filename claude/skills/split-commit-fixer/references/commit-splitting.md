# Commit Splitting Guide

## Goal

Turn one large dirty worktree into a small sequence of reviewable temporary commits without breaking coupled changes or hiding quality-gate failures, then collapse those temporary commits into a smaller final history once the full sequence lands cleanly.

## Preferred Grouping Order

1. Feature or subsystem code
2. Matching tests for the same feature
3. Matching docs for the same feature
4. Shared config and lockfiles only when one feature clearly owns them
5. Independent docs-only or tooling-only cleanup last

## Strong Signs Two Files Belong Together

- The files live under the same domain path such as `src/auth`, `apps/web/billing`, or `packages/ui/button`.
- One file is a test for the other.
- One file is documentation for the same domain.
- A rename or move touches both old and new locations of the same feature.
- A generated file exists solely because the feature changed.

## Strong Signs You Should Not Split Further

- A root manifest or lockfile changed while multiple features changed in the same worktree.
- A file is partially staged or has mixed staged and unstaged hunks.
- A shared utility or public API changed and multiple feature areas consume it.
- The same directory contains both the implementation and the gate fix that makes it pass.

## Suggested Commit Order

1. Feature batches with code and matching tests
2. Shared config or dependency batches
3. Standalone test-only batches
4. Standalone docs-only batches

Rebuild the batch plan after each commit. The remaining worktree is new evidence.

After the last planned batch, consolidate the temporary batch commits into the smallest final history that still describes the real net change. The default target is one final commit, but the final history can stay more fine-grained when the user asks for scope-level or checkpoint-level retention.

## Commit-Time Repair Rules

- Start from the first failing quality gate, not from generic cleanup.
- Use the batch's narrow gate list first, then widen to the full command chain after the local failure is fixed.
- Fix within the current batch boundary unless the failure proves a shared dependency.
- If the fix requires shared config or lockfile changes, fold them into the current batch and note the coupling.
- If a gate failure belongs to a different uncommitted feature, stop and regroup instead of hiding it in the current commit.

## Post-Commit Consolidation

1. Record the pre-split base commit before the first temporary batch commit.
2. Treat each per-batch commit as a checkpoint, not as the default final history.
3. Choose a granularity before the final rewrite:
   - `final`: one final commit for the whole change.
   - `scoped`: one final commit per generated consolidation group.
   - `checkpoint`: keep the temporary batch commits as-is.
4. Squash only after every planned batch has committed successfully and the worktree is clean.
5. Verify the checkpoint still matches the same lineage before squashing:
   - `git status --short` must be empty.
   - `git rev-list --count <base_commit>..HEAD` must match the completed batch count.
   - `git merge-base <base_commit> HEAD` must still equal `<base_commit>`.
6. Prefer deterministic non-interactive consolidation:
   - `git reset --soft <base_commit>`
   - For `final`, run one `git commit -m "<final conventional commit>"`.
   - For `scoped`, clear the index after the soft reset, then re-stage each generated consolidation group and commit them in order.
7. If any consolidation safety check fails, stop and keep the checkpoint commits instead of forcing a squash.

## Reporting Checklist

- State why each batch exists.
- Call out shared-risk files explicitly.
- Recommend a commit type and scope, but note when `feat` vs `fix` vs `refactor` is ambiguous.
- Tell the user what remains blocked or unverified after each batch.
- State whether the final squash ran, and if not, which safety check kept the checkpoint commits in place.
- State which granularity was selected, and list the scope-level groups when `scoped` granularity is used.
