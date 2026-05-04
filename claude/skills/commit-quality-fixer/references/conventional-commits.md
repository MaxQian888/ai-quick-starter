# Conventional Commits Quick Standard

## Format

```text
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Rules:
- Use imperative subject (`add`, `fix`, `refactor`), no ending period.
- Keep subject concise (usually <= 72 chars).
- Use one clear scope when it is obvious from changed files.
- Add body bullets for non-trivial changes.
- Add `BREAKING CHANGE:` footer when behavior is incompatible.

## Type Selection

- `feat`: Add user-facing functionality.
- `fix`: Correct a bug or regression.
- `refactor`: Improve structure without behavior changes.
- `perf`: Improve performance.
- `docs`: Update documentation only.
- `test`: Add or adjust tests only.
- `build`: Change build system or dependencies.
- `ci`: Change CI pipeline, hooks, or automation.
- `chore`: Routine maintenance with no product behavior change.
- `revert`: Revert a previous commit.

## Scope Heuristics

- Use module, package, or subsystem names (`api`, `auth`, `ui`, `build`).
- Prefer the smallest useful scope.
- Omit scope when changes span many unrelated areas.

## Message Templates

Simple:

```text
fix(parser): handle empty config values
```

With body:

```text
feat(auth): add refresh token rotation

- rotate refresh token on each successful renewal
- invalidate previous token family on replay detection
- add integration coverage for concurrent renewals
```

With footer:

```text
refactor(config): replace legacy env loader

- move runtime configuration into typed schema
- remove implicit fallback chain

BREAKING CHANGE: startup now fails fast when required env vars are missing
```

## Final Check Before Commit

- Header type matches main intent.
- Scope is specific and stable.
- Body explains why for complex changes.
- Footer includes issue links or breaking-change notes when needed.
