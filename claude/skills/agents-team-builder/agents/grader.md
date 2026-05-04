# Grader

## Purpose

Evaluate whether the agent correctly decomposed tasks before naming agents, kept parallelism honest, emitted structured artifacts, and respected workflow boundaries.

## Scoring Criteria

1. **Task Decomposition** (25%): Were tasks and dependencies identified before agent roles were assigned?
2. **Parallelism Honesty** (20%): Were only non-blocking tasks parallelized, with merge points explicit?
3. **Structured Output** (20%): Were Markdown plan, JSON truth-source, and `.toml` drafts all generated?
4. **Workflow Awareness** (20%): Was the correct workflow profile detected and applied (superpowers, OpenSpec, generic)?
5. **Install Safety** (15%): Were `.toml` files treated as drafts unless explicit `--install` was requested?

## Pass Threshold

Score >= 75% to pass.
