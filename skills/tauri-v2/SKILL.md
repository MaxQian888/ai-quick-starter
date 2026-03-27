---
name: tauri-v2
description: Use when working in a Tauri v2 app or `src-tauri` workspace and needing current guidance for shared `lib.rs` and `main.rs` entrypoints, `#[tauri::command]` registration, `@tauri-apps/api/core` IPC, capabilities and plugin permissions, desktop/mobile setup, or Tauri-specific failures such as `command not found`, `permission denied`, white screen, missing plugin wiring, or window label mismatch.
---

# Tauri v2

Treat Tauri v2 as five coupled surfaces: shared Rust entrypoint, frontend IPC, capability and permission wiring, plugin setup, and platform packaging. Work from the current official docs and CLI introspection instead of copying v1 snippets or stale blog posts.

## First Pass

1. Run `npm|pnpm tauri info` to confirm the project is actually on v2 and to capture the active CLI, Rust, Node, and platform state.
2. Inspect `src-tauri/src/lib.rs`, `src-tauri/src/main.rs`, `src-tauri/tauri.conf.json`, `src-tauri/capabilities/`, `src-tauri/Cargo.toml`, and the frontend package manifest before changing code.
3. If the task adds a plugin, prefer `npm|pnpm tauri add <plugin>` so the Rust crate, guest JS package, and generated ACL scaffolding stay aligned.
4. If permissions are unclear, use `tauri permission ls` and `tauri permission add <permission-id>` instead of guessing identifiers from memory.

## Symptom Map

| Symptom | Check First | Common Root Cause |
| --- | --- | --- |
| `command not found` | `lib.rs` `invoke_handler` list and frontend `invoke(...)` name | Command exists but is not registered, or the frontend name is wrong |
| `permission denied` | `src-tauri/capabilities/*.json`, plugin permissions, window label | Capability file missing, wrong permission ID, or `windows` / `webviews` do not match |
| White screen or missing frontend | `build.devUrl`, `build.frontendDist`, `beforeDevCommand`, CSP | Frontend dev/build path is wrong or the web assets never loaded |
| Plugin compiles but API call fails | `.plugin(...)`, guest package import, plugin page support matrix | Rust plugin not registered, JS package missing, or plugin unsupported on target platform |
| Mobile build or runtime breakage | `lib.rs` shared `run()`, mobile entry attribute, plugin platform notes | Desktop-only assumptions leaked into mobile or entrypoint is not shared |

## Workflow

### 1. Normalize the entrypoint layout

- Keep the real builder in `src-tauri/src/lib.rs`.
- Keep `src-tauri/src/main.rs` minimal and let it call `app_lib::run()`.
- Use `#[cfg_attr(mobile, tauri::mobile_entry_point)]` on `run()` so desktop and mobile share the same builder path.
- If the repo still keeps business logic in `main.rs`, move the shared pieces before touching plugins or commands.

### 2. Wire commands before touching the frontend

- Annotate every callable function with `#[tauri::command]`.
- Register every command in `tauri::generate_handler![...]`.
- Use owned types such as `String`, `Vec<T>`, or explicit structs for async command arguments; avoid borrowed parameters such as `&str`.
- Return `Result<T, E>` for failure paths and serialize errors explicitly.
- When commands live in separate modules, mark them `pub` there and register them with their full module path in `generate_handler!`.

### 3. Choose the right IPC primitive

- Use `invoke` plus commands for request-response work.
- Use events for low-volume notifications or broadcast-style updates.
- Use `Channel` for ordered, higher-throughput streaming such as download progress, logs, or child-process output.
- Do not use events for large or high-frequency payloads if a channel fits better.
- Do not forget listener cleanup on the frontend; Tauri only auto-cleans on page reload, not on SPA component unmount.

### 4. Add capabilities and permissions deliberately

- Put capability files under `src-tauri/capabilities/`.
- Match `windows` or `webviews` labels to the actual labels used by the app.
- Start from `core:default`, then add only the plugin or app permissions the feature needs.
- Scope dangerous permissions instead of granting broad access by default.
- If custom app commands need their own ACL surface, add `src-tauri/permissions/*.toml` and reference those permission IDs from capabilities.

### 5. Add plugins as a three-part change

- Add the plugin through `tauri add` when possible.
- Register the plugin in `tauri::Builder::default().plugin(...)` inside `lib.rs`.
- Install and import the matching guest package such as `@tauri-apps/plugin-dialog`.
- Re-check the plugin page for platform notes before assuming parity across desktop and mobile.
- Use the plugin page or `tauri permission ls` to confirm the exact permission IDs instead of relying on old examples.

### 6. Verify config and packaging assumptions

- `build.devUrl` and `build.beforeDevCommand` must match the active frontend dev server.
- `build.frontendDist` and `build.beforeBuildCommand` must match the production frontend output.
- `app.windows[].label` must stay consistent with capability targeting.
- `bundle` fields should reflect the actual packaging target instead of cargo-culting a different app's config.
- For mobile plugins, also read the plugin page's Android manifest or iOS privacy requirements before claiming the setup is complete.

## Guardrails

- Do not use `@tauri-apps/api/tauri`; in v2 the normal command entrypoint is `@tauri-apps/api/core`.
- Do not assume a command exists just because it is annotated; if it is absent from `generate_handler![]`, it is not callable.
- Do not hardcode shell, fs, or dialog permission IDs from memory when the CLI can list them.
- Do not assume desktop plugin behavior automatically works on Android or iOS.
- Do not pass borrowed types into async commands unless you deliberately apply one of the documented workarounds.
- Do not report success until the exact failing path is re-run after capability or plugin changes.

## References

- Read `references/triage-checklist.md` when the failure is still ambiguous.
- Read `references/entrypoints-and-config.md` when the task touches `lib.rs`, `main.rs`, `tauri.conf.json`, or desktop/mobile layout.
- Read `references/ipc-patterns.md` before choosing between commands, events, and channels.
- Read `references/plugin-permissions.md` before adding or widening plugin access.
- Read `references/official-sources.md` when you need the exact official page to open.
