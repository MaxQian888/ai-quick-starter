# Commit Splitting Guide

## Goal

Turn one large dirty worktree into a small sequence of reviewable commits without breaking coupled changes or hiding quality-gate failures.

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

## Commit-Time Repair Rules

- Start from the first failing quality gate, not from generic cleanup.
- Use the batch's narrow gate list first, then widen to the full command chain after the local failure is fixed.
- Fix within the current batch boundary unless the failure proves a shared dependency.
- If the fix requires shared config or lockfile changes, fold them into the current batch and note the coupling.
- If a gate failure belongs to a different uncommitted feature, stop and regroup instead of hiding it in the current commit.

## Reporting Checklist

- State why each batch exists.
- Call out shared-risk files explicitly.
- Recommend a commit type and scope, but note when `feat` vs `fix` vs `refactor` is ambiguous.
- Tell the user what remains blocked or unverified after each batch.
