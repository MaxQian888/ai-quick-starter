# Change Mapping

Use the helper output as a ranking aid, not as an infallible oracle.

## Inputs

The helper accepts changed implementation paths from:

- repeated `--changed-file` flags,
- `--changed-file-list <file>`,
- or git status auto-detection when `--project-root` is a git checkout.

Prefer explicit paths when the user already named the failing screen, route, or feature subtree.

## Matching Heuristic

`scripts/build_e2e_change_plan.py` scores each spec by:

- normalized path-token overlap between the changed file and the spec,
- token overlap between the changed file and the spec file content,
- extra weight for shared directory tokens,
- extra weight when the changed filename stem appears in the spec stem.

Examples:

- `src/features/auth/login-form.tsx` should rank `e2e/auth-login.spec.ts` above unrelated specs.
- `src/features/auth/login-form.tsx` can still rank `e2e/session.spec.ts` if the spec body clearly describes a login-form journey.
- `src/features/billing/invoice-list.tsx` with no invoice-like spec should land in `coverage_gaps`.

## Review Rules

- Read the top-ranked spec names and their `reasons` before editing anything.
- If two specs have similar scores, inspect both and choose the one that owns the more complete user flow.
- If a changed file is infrastructure-only and does not alter a user-visible journey, a `coverage_gap` may be acceptable. Record that reasoning in your final report.
- If a changed path represents a new route or a new major branch, prefer a new or extended E2E path instead of forcing it into a weakly related spec.

## False Positive Patterns

Watch for accidental token overlap from generic names such as:

- `settings`
- `page`
- `modal`
- `dialog`
- `form`

When generic overlap dominates, review the directory context and actual user journey before accepting the suggestion.

## Nested App Notes

When the runner lives under a nested app such as `apps/web`:

- expect `runner.working_directory` to point at that subtree,
- read `spec_paths` as repo-relative paths,
- remember that `execution_plan.targeted_command` rewrites the spec argument relative to the detected working directory.
