# Example Prompts

Use this file to sanity-check triggering. These are representative prompt shapes that should either load this skill or route somewhere narrower.

## Should Trigger This Skill

- "Audit `src/features/auth` and tell me what we should optimize before refactoring it."
- "Look at this checkout flow and give me a prioritized optimization plan, not code changes yet."
- "Study the current notification module, compare it with current best practices, and tell me what to improve first."
- "Review the settings page implementation for maintainability, type safety, and missing tests, then draft a plan."
- "Inspect this API handler chain and tell me whether the current implementation has performance or error-handling drift."

## Usually Better Routed Elsewhere

- "Fix the failing tests in `src/features/auth`."
  Route to `$build-project-fixer`.

- "Compare the spec with the current implementation and list missing requirements."
  Route to `$feature-gap-requirements-auditor`.

- "Which part of this whole repository should we optimize first?"
  Route to `$project-optimization-opportunity-auditor`.

- "I don't even know where this feature lives. Map the architecture first."
  Route to `$project-architecture-design-analyzer`.

## Prompt Smells

These prompts often sound like this skill, but need one more scoping pass first:

- "Optimize the dashboard."
  Clarify which dashboard surface and what kind of optimization.

- "Review performance."
  Clarify the feature boundary, runtime path, and whether a plan or a fix is expected.

- "Make this module better."
  Clarify whether the user wants a plan, a refactor, or a requirements audit.
