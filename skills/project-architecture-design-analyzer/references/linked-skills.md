# Linked Skills

Use this file when the architecture snapshot is not the final answer and you need to choose the right follow-on skill.

## Mapping Rules

### `$codebase-indexing-assistant`

Use when:

- the repository is still too large or unfamiliar,
- the user wants a broader reading order,
- or the architecture report needs more file-level coverage.

Do not use it as a substitute for feature tracing or runtime verification.

### `$feature-call-chain-mapper`

Use when:

- the user names a feature, request path, API flow, or handler chain,
- `--focus` is already present,
- or the next step is "show me how this actually flows."

Prefer it after this skill has already narrowed the architecture surface.

### `$project-ai-context-initializer`

Use when:

- root `AGENTS.md` or `CLAUDE.md` is missing,
- architecture docs are thin or absent,
- or the team needs durable navigation docs and Mermaid maps.

This is the right follow-up when the architecture findings should become shared documentation instead of a one-off report.

### `$build-project-fixer`

Use when:

- manifest commands need to be verified,
- runtime behavior matters more than static structure,
- or build, lint, test, and typecheck gates may contradict the inferred architecture.

Do not present command hints from this skill as verified without this follow-up.

### `$project-skill-builder`

Use when:

- the repository will be revisited repeatedly,
- the architecture snapshot surfaced stable repo-specific guardrails,
- or the user wants to preserve local truth as a reusable skill package.

This turns one-off analysis into a repeatable repo-local onboarding surface.

## Tie-Break Rules

- Prefer `$feature-call-chain-mapper` over `$codebase-indexing-assistant` when the question is already feature-bounded.
- Prefer `$project-ai-context-initializer` over `$project-skill-builder` when the problem is missing documentation rather than repeatability.
- Prefer `$build-project-fixer` whenever static design claims need runtime proof.
