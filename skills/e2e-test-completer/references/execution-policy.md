# Execution Policy

Use dry-run planning to choose the narrowest trustworthy E2E command before executing anything expensive.

## Discover

Start with:

```bash
uv run --python 3.11 scripts/build_e2e_change_plan.py --project-root . --mode discover --json
```

Do this before editing tests when the repo's E2E stack or main command is unclear.

## Plan

Use `--mode plan` after you know which implementation files changed.

The goal is to answer:

- which runner owns the suite,
- whether the runner actually lives in a nested app subtree,
- which existing specs are closest,
- whether coverage gaps remain before execution.

If your work is branch-based, prefer `--git-base <rev>` over plain worktree status so the change list reflects the intended comparison point.

## Simulate

Use `--mode simulate` to obtain:

- `execution_plan.targeted_command`
- `execution_plan.full_command`
- `execution_plan.targeted_specs`

`simulate` is a dry run. It validates scope selection, not runtime success.

## Execute

Prefer this order:

1. targeted command from `execution_plan.targeted_command`,
2. broader E2E command from `execution_plan.full_command`,
3. repo-level validation chain only after the E2E scope is stable.

If `runner.working_directory` is non-empty, execute the generated commands exactly as emitted instead of stripping the directory prefix.

## Stop Conditions

Stop and reassess when:

- the helper cannot detect a runner,
- all candidate matches are obviously false positives,
- the repo has multiple E2E stacks and auto-detection picked the wrong one,
- the targeted command requires environment setup the current repo cannot satisfy yet.

In those cases, inspect the real manifests, configs, and CI workflow before guessing a command line.
