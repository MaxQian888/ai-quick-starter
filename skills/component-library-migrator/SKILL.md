---
name: component-library-migrator
description: >
  Make sure to use this skill whenever the user wants to migrate UI components to
  a new component library, replace native HTML elements with shadcn/ui, MUI,
  Ant Design, Chakra UI, or HeroUI, audit a React directory for migration
  opportunities, or modernize an existing component set. Also trigger for
  "switch to shadcn," "replace buttons with MUI," "audit components for library
  migration," "migrate to a design system," or "component library upgrade."
  Covers synonyms like "UI migration," "component replacement," "design system
  adoption," "library swap," and "JSX modernization." Use it even when the user
  only says "I want to use shadcn in my project" or "can we switch to MUI."
---

# Component Library Migrator

Audit the target directory before editing JSX. Only migrate files that the report marks as safe.

## Adaptive Detection

Before auditing, detect the project context:

- Identify the framework: React, Next.js, Vue, or other.
- Check `package.json` for existing UI library dependencies.
- Detect styling approach: CSS modules, Tailwind, styled-components, or CSS-in-JS.
- Confirm the target library is built-in (`shadcn/ui`, `mui`, `ant-design`, `chakra-ui`, `heroui`) or unsupported.
- Check for existing design-system wrappers or custom component layers that may block migration.

## Workflow

1. Confirm the repository root, exact target path, and requested target library.
2. Run the audit before manually reading many component files:

```bash
python scripts/build_component_library_migration_audit.py --root <repo> --target <component-dir> --library <target-library>
```

3. Read the JSON output first.
4. Check `target_library.is_builtin` and `mode`:
   - built-in target plus `auto-edit`: direct edits are allowed, but only inside `safe_fix_plan`.
   - non-built-in target plus `audit-only`: do not generate direct migration edits in version one.
5. Review `component_findings`, `candidate_mappings`, `blocked_reasons`, and `forbidden_actions`.
6. Edit only the files listed in `safe_fix_plan`.
7. Re-run targeted checks for the touched components or the nearest existing repository validation command.
8. Report changed files, blocked files, and unverified risk areas explicitly.

## Built-In Targets

Built-in targets supported in version one:

- `shadcn/ui`
- `mui`
- `ant-design`
- `chakra-ui`
- `heroui`

Read [references/builtin-libraries.md](references/builtin-libraries.md) for canonical names, aliases, and first-pass mapping coverage.

## Decision Rules

- Prefer safe native-element migrations such as `button`, `input`, `textarea`, and `select`.
- Treat custom wrapper imports as blocked until a human or a deeper repository pass confirms the wrapper seam.
- Treat overlays, drawers, dialogs, and stateful composite widgets as blocked unless the audit explicitly marks them safe.
- If the target library is unsupported, keep the task in audit-only mode and provide suggestions instead of direct edits.
- If the report finds no safe candidates, stop and explain why rather than widening the migration scope.

## Guardrails

- Do not broaden edits beyond the requested target path unless the audit proves a shared wrapper or import seam must change.
- Do not auto-migrate complex widgets, local design-system wrappers, or behavior-heavy form components in version one.
- Do not rewrite styling broadly just to resemble the target library.
- Do not mix multiple migration strategies in the same file.
- Do not claim migration success from the static audit alone.

## What To Read In The Report

- `target_library`: canonical target name, built-in support flag, and mode implications.
- `component_findings`: per-file status and reasons.
- `candidate_mappings`: low-risk component replacements detected by the audit.
- `safe_fix_plan`: the only file-level edits approved for direct migration.
- `blocked_reasons`: why some files require manual follow-up.
- `forbidden_actions`: actions that would over-expand or de-risk the migration incorrectly.

## Examples

**Audit for shadcn/ui migration:**
```bash
python scripts/build_component_library_migration_audit.py --root . --target src/components --library shadcn/ui
```

**Audit for MUI with JSON output:**
```bash
python scripts/build_component_library_migration_audit.py --root . --target app/ui --library mui --json
```

## References

- Read [references/builtin-libraries.md](references/builtin-libraries.md) for built-in target support and mapping boundaries.
- Read [references/detection-playbook.md](references/detection-playbook.md) for candidate rules, block conditions, and stop signals.
- Read [references/output-schema.md](references/output-schema.md) for the JSON and Markdown report contract.
