# Entrypoints and Config

Use this file when the task touches shared Rust startup, frontend build hooks, or desktop/mobile shape.

## Minimum structure to expect

```text
project/
  src/
  src-tauri/
    src/
      lib.rs
      main.rs
    tauri.conf.json
    capabilities/
```

On mobile-enabled projects you should also expect generated platform folders under `src-tauri/gen/`.

## Entrypoint rules

- Keep the shared `run()` function in `src-tauri/src/lib.rs`.
- Put `#[cfg_attr(mobile, tauri::mobile_entry_point)]` on that `run()` function.
- Keep `src-tauri/src/main.rs` minimal so desktop simply delegates into the shared `run()`.
- Register plugins, commands, managed state, and setup hooks in `lib.rs`, not in a desktop-only path.

## Command layout rules

- Commands defined directly in `lib.rs` should stay non-`pub`.
- Commands defined in another module should be `pub` in that module and registered with their module path in `generate_handler!`.
- Command names must remain unique across modules.

## `tauri.conf.json` fields to verify

### Build

- `build.devUrl`: points at the actual frontend dev server, or leave it unset if the project intentionally uses the built-in static server path.
- `build.beforeDevCommand`: starts the frontend dev server when `devUrl` is used.
- `build.frontendDist`: points at the production frontend build output relative to `src-tauri`.
- `build.beforeBuildCommand`: produces the assets expected by `frontendDist`.

### App

- `app.windows[].label`: must match the labels used by capabilities and any window-targeted event logic.
- `app.security.csp`: should be checked when remote resources or injected scripts are involved.
- If a repo relies on copied config fields you cannot find in the current docs, re-open the docs before preserving them.

### Bundle

- Confirm the bundle target and icon paths match the real app.
- Do not keep cross-project leftovers like another app's identifier or product name.

## Mobile-specific checks

- Desktop window assumptions do not automatically apply to Android and iOS.
- Plugin pages often include extra Android manifest or iOS privacy-file work; check those before calling the mobile path complete.
- Keep business logic out of generated `gen/android` and `gen/apple` code when possible.

## Good verification order

1. `tauri info`
2. confirm frontend dev command or dist path
3. verify `lib.rs` owns the shared builder
4. verify capability target labels
5. reproduce the exact failing interaction on the intended platform
