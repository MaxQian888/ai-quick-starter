# Blind Spots

Use these categories when explaining why a reported chain may be incomplete.

## Common Static-Analysis Gaps

- Dynamic dispatch and reflection
- Decorators, annotations, and framework registration
- Config-driven module loading
- Generated code
- Cross-process and remote-service handoffs
- Runtime dependency injection containers

## Reporting Rules

- Always include blind spots in the final artifact.
- Prefer concrete language over generic disclaimers.
- If there were no observed edges, say that the chain is mostly heuristic.
- If the feature term is broad or ambiguous, say that matching may have promoted unrelated modules.

## Good Wording

- "Observed edges cover the direct import-and-call path, but framework registration may add hidden entrypoints."
- "No direct call edge was observed, so this report falls back to file and symbol heuristics."
- "The chain crosses module boundaries cleanly in source text, but remote-service transitions remain outside this report."
