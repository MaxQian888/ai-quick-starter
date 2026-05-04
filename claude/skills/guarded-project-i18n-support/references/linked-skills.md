# Linked Skills

Use this file when the project-level i18n plan is ready for component-level execution or when the audit reveals follow-up needs.

## `$guarded-component-i18n-fix`

Use when:
- the project plan identifies specific components or directories that need localization,
- the user wants to fix hardcoded strings in a bounded surface rather than the whole app.

This is the natural downstream handoff for scoped i18n work.

## `$build-project-fixer`

Use when:
- installing i18n dependencies or modifying config files breaks the build,
- runtime verification is needed after wiring middleware, providers, or locale loaders.

## `$component-unit-test-completer`

Use when:
- localized components need corresponding test updates for new locales or translated strings.

## Routing Rules

- Route to `$guarded-component-i18n-fix` only after the project-level strategy is clear.
- Do not skip `$guarded-component-i18n-fix` and bulk-convert strings project-wide from this skill.
- If the repository already has a dominant i18n stack, always extend it rather than introducing a second system.
