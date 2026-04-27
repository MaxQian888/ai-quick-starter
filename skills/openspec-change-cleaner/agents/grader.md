# Grader

## Purpose

Evaluate whether the agent correctly audited active OpenSpec changes, compared artifacts against the latest implementation, and applied conservative cleanup only with explicit evidence.

## Scoring Criteria

1. **Audit First** (25%): Did the agent run the cleanup report before editing any artifacts?
2. **Implementation Comparison** (25%): Did the agent inspect actual code paths, tests, and workflows rather than relying on memory?
3. **Conservative Cleanup** (25%): Were archive entries only cleaned when proven placeholder-only, duplicated, or empty?
4. **Validation** (25%): Did the agent re-run `openspec validate` after every material refresh?

## Pass Threshold

Score >= 75% to pass. Archiving a broken change without repair is an automatic critical failure.
