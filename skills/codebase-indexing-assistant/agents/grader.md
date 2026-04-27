# Grader

## Purpose

Evaluate whether the agent correctly ran the indexer before broad file reads, used the generated report to narrow scope, and treated heuristic outputs as suggestions rather than facts.

## Scoring Criteria

1. **Index First** (30%): Did the agent run `build_code_index.py` before opening many files manually?
2. **Narrow Reading** (25%): Were only the smallest file sets opened based on `reading_order` or `entry_candidates`?
3. **Scope Refinement** (20%): Was `--focus`, `--include`, or `--exclude` used when the first pass was too broad?
4. **Honesty** (25%): Were heuristic outputs labeled as suggestions, and were claims separated from guesses?

## Pass Threshold

Score >= 75% to pass.
