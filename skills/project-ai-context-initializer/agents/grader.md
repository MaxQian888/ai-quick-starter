# Grader

## Purpose

Evaluate whether the agent correctly dispatched subagents in sequence, generated root and module docs with required features, and reported coverage honestly.

## Scoring Criteria

1. **Subagent Sequence** (25%): Was a datetime subagent dispatched first, followed by the architect subagent?
2. **Doc Features** (25%): Did generated docs include purpose, breadcrumbs, Mermaid diagrams, key files, read order, and skip notes?
3. **Module Selection** (20%): Were 3-8 high-value modules chosen rather than documenting every directory?
4. **Coverage Honesty** (20%): Did the summary explicitly report scanned, covered, and skipped areas with reasons?
5. **Incremental Updates** (10%): Were existing high-quality docs merged incrementally rather than blindly rewritten?

## Pass Threshold

Score >= 75% to pass.
