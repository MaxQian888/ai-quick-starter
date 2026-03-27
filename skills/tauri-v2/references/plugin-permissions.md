# Plugin Permissions

Use the official plugin pages and CLI introspection together. The safest pattern is:

1. `tauri add <plugin>`
2. Register `.plugin(tauri_plugin_<name>::init())` in `src-tauri/src/lib.rs`
3. Install or confirm the matching guest package such as `@tauri-apps/plugin-dialog`
4. Run `tauri permission ls`
5. Add only the needed permission IDs to `src-tauri/capabilities/*.json`

## Capability file anatomy

The current capability schema is centered on:

- `identifier`
- `description`
- `windows` or `webviews`
- `permissions`
- optional `platforms`
- optional `remote`

Keep a capability focused on the exact window or webview that needs access. If labels do not match, the permission change does nothing.

## CLI commands worth using

- `tauri add <plugin>`: add the plugin in the supported way
- `tauri permission ls`: list the permission IDs available to the app
- `tauri permission add <permission-id>`: add a permission to existing capabilities
- `tauri capability new`: scaffold a new capability file when you need a fresh boundary

## Dialog plugin

Official page: `https://tauri.app/plugin/dialog/`

### What to remember

- Setup expects `tauri_plugin_dialog::init()` in `lib.rs`.
- JavaScript guest package is `@tauri-apps/plugin-dialog`.
- Android and iOS do not support folder picking.
- On Android and iOS the returned path shape is not the same as on desktop, so do not assume a plain desktop filesystem path everywhere.

### Current default permission set

The official page says the default dialog permission set includes:

- `dialog:allow-ask`
- `dialog:allow-confirm`
- `dialog:allow-message`
- `dialog:allow-save`
- `dialog:allow-open`

Use these names as examples, but still confirm with `tauri permission ls` in the real project.

## File System plugin

Official page: `https://tauri.app/plugin/file-system/`

### What to remember

- Setup expects `tauri_plugin_fs::init()` in `lib.rs`.
- JavaScript guest package is `@tauri-apps/plugin-fs`.
- Rust-side file manipulation should still use `std::fs` or `tokio::fs`; the plugin mainly exposes frontend-safe FS access plus scope helpers.
- The default permission set is app-directory oriented, not global disk access.

### Current official patterns

- Capability example uses `fs:default` plus a scoped permission object such as:
  - `identifier: "fs:allow-exists"`
  - `allow: [{ "path": "$APPDATA/*" }]`
- The page's permission table uses app-directory specific IDs such as:
  - `fs:allow-appdata-read`
  - `fs:allow-appdata-write`
  - `fs:allow-appdata-read-recursive`
  - `fs:allow-appdata-write-recursive`

Do not rely on older broad IDs like `fs:allow-read-file` unless the live project actually lists them.

### Mobile caveats

- Android access outside app folders may require external-storage manifest permissions.
- iOS requires a `PrivacyInfo.xcprivacy` entry for file timestamp API usage according to the plugin page.

## Shell plugin

Official page: `https://tauri.app/plugin/shell/`

### What to remember

- Setup expects `tauri_plugin_shell::init()` in `lib.rs`.
- JavaScript guest package is `@tauri-apps/plugin-shell`.
- Android and iOS only allow opening URLs through the `open` path; they do not behave like full desktop shell execution.
- The docs explicitly point `shell.open` users to the newer Opener plugin when that is the only need.

### Current official permission examples

- Default shell permission includes open functionality with reasonable scope.
- The permission table includes IDs such as:
  - `shell:allow-open`
  - `shell:allow-execute`
  - `shell:allow-spawn`
  - `shell:allow-kill`
  - `shell:allow-stdin-write`

The official scoped execute example includes fields such as:

- `identifier`
- `allow`
- `name`
- `cmd`
- `args`
- `sidecar`

If you need command execution, keep the scope narrow and review it like production security code.

## App-defined permissions

When plugin permissions are not enough and your own commands need fine-grained ACL, add `src-tauri/permissions/*.toml`.

Use app-defined permissions when:

- only a subset of custom commands should be callable
- a custom command needs a scoped argument boundary
- you want a reusable permission identifier across multiple capability files

Use the permission schema reference for field shape, not old examples copied from random repos.
