# Coverage Playbook

Increase E2E coverage by user-flow risk, not by raw spec count.

## Priorities

Start with flows changed by the latest implementation work:

1. primary happy path,
2. one high-risk branch introduced or modified by the change,
3. a failure or empty-state branch only when the implementation touched it directly.

## High-Value Branches

Prefer adding assertions around:

- auth gates,
- routing and redirect behavior,
- form validation,
- permission states,
- destructive actions,
- asynchronous loading transitions that gate the user journey.

## Good Coverage Expansion

- Extend the spec that already owns the journey.
- Reuse existing fixtures, seeded data, and helper commands.
- Assert user-visible outcomes rather than implementation details.
- Keep setup small so the new branch remains easy to diagnose.

## Bad Coverage Expansion

- Creating a new spec for every tiny component-level tweak.
- Adding snapshot-like assertions that do not protect behavior.
- Testing the same happy path twice under different filenames.
- Hiding flaky setup behind retries instead of fixing the real instability.

## Gap Triage

When the helper reports `coverage_gaps`:

- confirm whether the changed file affects a user-visible flow,
- inspect the nearest existing spec for reuse,
- add or extend the minimum E2E path that proves the changed behavior,
- then re-run the targeted command before broadening scope.
