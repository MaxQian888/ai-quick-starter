# Standards Discovery

Use this order when deciding which style rules the simplification must follow:

1. Direct user instruction
2. `CLAUDE.md`, `AGENTS.md`, or equivalent repo-local agent guidance
3. `CONTRIBUTING.md` and nearby module docs
4. Lint, formatter, typecheck, and test config
5. The nearest well-maintained sibling files

If two sources conflict, the more local and more explicit source wins.

## Fallback Rules

If the repository does not state a rule explicitly:

- preserve the dominant local pattern instead of importing a generic best practice,
- prefer explicit names over shortened aliases,
- prefer straightforward control flow over compact expressions,
- keep imports grouped and stable,
- and keep React, async, and error-handling patterns aligned with the surrounding files.

## When To Apply The Provided Defaults

The user-provided defaults below are safe only when they do not conflict with repo-local standards:

- prefer ES modules with proper import sorting and extensions,
- prefer `function` over arrow functions for top-level declarations,
- add explicit return types for top-level functions,
- use explicit React `Props` types,
- avoid `try/catch` when a clearer control-flow alternative exists,
- and reject nested ternary operators.

If the repository already uses a different convention consistently, the repository wins.
