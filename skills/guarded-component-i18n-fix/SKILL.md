---
name: guarded-component-i18n-fix
description: >
  Use this skill when auditing or fixing internationalization (i18n) in a specific component or directory.
  It detects the repository's existing i18n stack first — whether react-i18next, next-intl, vue-i18n, gettext,
  or a custom hook — and only then plans safe, minimal fixes. Make sure to use this skill whenever you need
  to localize components, hardcoded strings, or UI text, especially if the repository already has an i18n
  setup and you want to avoid introducing a duplicate or conflicting framework.
---

# Guarded Component I18n Fix

Start by detecting the repository's i18n stack. Only plan or apply minimal fixes after the stack is identified with sufficient confidence.

## Adaptive Detection

Before running the audit, scan for:
- `package.json` to detect framework (React, Vue, Angular, Svelte) and existing i18n libraries
- `i18n.config.*`, `next.config.*`, `vue.config.*` for i18n bootstrap files
- Existing locale directories (`locales/`, `messages/`, `lang/`, `i18n/`)
- Translation hooks or helpers already in use (`useTranslation`, `useIntl`, `$t`, `gettext`)
- Test framework in use (jest, vitest, playwright) to plan verification

## Workflow

1. Confirm the repository root and the exact target directory or file.
2. Run the audit first, before diving into individual component files:

```bash
uv run --python 3.11 scripts/build_component_i18n_audit.py --root <repo> --target <component-dir>
```

3. Read the JSON output first; the Markdown output is for human-readable review.
4. Check `selected_system.confidence` before making any code changes:
   - `high` or `medium`: only reuse the detected stack.
   - `low`: stop and ask for confirmation, or manually inspect the existing i18n entrypoints.
5. Only fix the files listed in `safe_fix_plan`.
6. After editing, verify against an existing localized component or the repository's test stack. Don't consider the static audit alone as proof of success.

## Guardrails

- Don't introduce a second i18n framework into the target directory.
- Don't add a new provider, bootstrap file, locale loader, or message registry unless the repository already uses one.
- Don't bulk-rewrite every string match. Prefer the smallest safe subset in one directory.
- Don't create new translation key conventions when the repository already has an established naming pattern.
- Treat `mixed-patterns` as a normalization task, not a greenfield rewrite.

## How to Read the Report

- `selected_system`: the most likely repository stack, along with confidence level and evidence.
- `detected_systems`: competing stacks with raw score context.
- `component_findings`: per-file statuses like `needs-localization`, `mixed-patterns`, and `blocked`.
- `safe_fix_plan`: the only files the audit deems safe to modify.
- `forbidden_actions`: actions that could duplicate or break the existing i18n setup.
- `blind_spots`: cases the static scanner can't reliably detect.

## Decision Rules

- If one framework is clearly dominant, reuse its hook, helper, namespace, and locale layout.
- If detection is ambiguous, inspect existing localized components and the i18n entrypoint before editing.
- If a file already uses translation APIs but still contains raw strings, keep the existing API and normalize only the remaining literals.
- If no framework is detected, focus on diagnosis and evidence gathering rather than speculative i18n wiring.

## References

- Read [references/detection-playbook.md](references/detection-playbook.md) for stack-identification heuristics and stop conditions.
- Read [references/output-schema.md](references/output-schema.md) for the report contract.
- Read [references/official-sources.md](references/official-sources.md) when you need primary-source terminology or API naming.

## Examples

**Example 1: Localize hardcoded strings in a React component**
```
User: "The Header component in src/components has hardcoded English text. Can you fix it?"
Agent: Run the audit script on src/components, check selected_system.confidence, reuse the detected react-i18next stack, and only modify files in safe_fix_plan while keeping existing key conventions.
```

**Example 2: Audit an entire directory for i18n gaps**
```
User: "Audit the dashboard module for missing translations."
Agent: Run the audit on the dashboard directory, read the JSON output, classify findings (needs-localization, mixed-patterns, blocked), and present the safe_fix_plan before making any edits.
```
