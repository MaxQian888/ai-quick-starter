# Grader Instructions

## Purpose

Evaluate outputs from the `e2e-test-completer` skill for accuracy, safety, and coverage awareness.

## Grading Criteria

1. **Runner Detection** — Correctly identifies Playwright or Cypress and respects existing runner conventions.
2. **Change Mapping** — Changed files are accurately mapped to affected specs with plausible rankings.
3. **Coverage Gap Awareness** — Uncovered flows are flagged; new specs are created only when necessary.
4. **Assertion Integrity** — Existing assertions are not deleted or weakened to make tests pass.
5. **Verification Discipline** — Targeted verification is run before widening; simulate mode is not claimed as proof of passing.

## Scoring

- **Pass**: All criteria met; tests are synced safely and coverage gaps are closed appropriately.
- **Partial**: Minor issues (e.g., one false-positive spec match, slightly incomplete coverage gap list).
- **Fail**: Major issues (e.g., introducing a new runner when one exists, weakening assertions, claiming simulate means pass).
