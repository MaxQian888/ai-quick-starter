# Import Rewrite Policy

The executor rewrites only target-local relative imports and exports.

## Rewrite Scope

- files inside the planned `target_directory`
- moved files after relocation
- local consumers still inside the target directory
- barrel exports inside the target directory

## What To Rewrite

- relative `import ... from './x'`
- relative `export ... from './x'`
- dynamic `import('./x')` when it points at a moved file

## What Not To Rewrite

- absolute aliases such as `@/components/...`
- package imports
- files outside the target directory
- unrelated refactors or naming changes

## Stop Conditions

- if the move graph would require cross-package or cross-app rewrites
- if import syntax is too dynamic to update safely with static rewriting
- if the target directory changed since planning and relative paths are no longer trustworthy
