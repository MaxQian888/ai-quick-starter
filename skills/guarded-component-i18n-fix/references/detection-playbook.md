# Detection Playbook

## Goal

Identify the repository's existing i18n stack before editing any component directory.

## Signal Order

1. Package and dependency manifests
2. Existing imports and hooks in localized components
3. Locale-loading entrypoints and message file layout
4. Existing translation key naming patterns
5. Only after the above: target-directory hardcoded-string scan

## Stop Conditions

Pause automatic fixing when any of these is true:

- Two frameworks score similarly and neither is dominant
- The target directory is not the real component boundary
- The repository uses a custom translation wrapper but the wrapper contract is still unclear
- The target files already mix multiple patterns and need human normalization decisions

## Safe Edit Bias

Prefer:

- Reusing the same hook or helper already present nearby
- Reusing the same namespace shape and key naming style
- Fixing one file or one component cluster at a time

Avoid:

- Adding a second provider
- Adding a second locale tree
- Converting the whole repository from a single directory request
