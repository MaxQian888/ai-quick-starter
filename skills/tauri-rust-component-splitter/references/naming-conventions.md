# Naming Conventions

Use these rules when reviewing the planner output or choosing scaffold file names.

## Rust Naming Rules

- Modules and file names: `snake_case`
- Functions: `snake_case`
- Types (`struct`, `enum`, `trait`): `PascalCase`
- Constants and static values: `SCREAMING_SNAKE_CASE`

## Preferred Tauri Module Names

- Commands: `<context>_commands.rs`
- State: `<state_name>.rs`
- Services: `<service_name>.rs`
- Platform adapters: `<adapter_name>.rs`
- Models: `<type_name>.rs`

Choose explicit responsibility names such as `app_commands.rs`, `notification_service.rs`, or `window_platform.rs`.

## Naming Anti-Patterns

- `common.rs`
- `helpers.rs`
- `misc.rs`
- `manager.rs` when it hides multiple responsibilities
- Mixed-casing names such as `DoThing`, `helperThing`, or `Windowmanager`

These names hide ownership and make later extraction harder.

## Rename Guidance

- Prefer one reason to change per module name.
- Preserve existing public API names until a later migration pass if callers depend on them.
- Rename generic modules before or during extraction so the destination file names stay stable.
- If a symbol's purpose is still unclear after reading the file, stop and keep the finding visible in the plan instead of forcing a rename.
