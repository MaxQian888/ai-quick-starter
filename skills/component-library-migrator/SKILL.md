---
name: component-library-migrator
description: Use when inspecting a React component directory to find safe opportunities to replace existing UI elements with a target component library, especially when Codex must audit first, support built-in targets like shadcn/ui, MUI, Ant Design, Chakra UI, and HeroUI, and only apply minimal evidence-backed edits.
---

# Component Library Migrator

Audit the target directory before editing JSX. Only migrate files that the report marks as safe.

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

## References

- Read [references/builtin-libraries.md](references/builtin-libraries.md) for built-in target support and mapping boundaries.
- Read [references/detection-playbook.md](references/detection-playbook.md) for candidate rules, block conditions, and stop signals.
- Read [references/output-schema.md](references/output-schema.md) for the JSON and Markdown report contract.
