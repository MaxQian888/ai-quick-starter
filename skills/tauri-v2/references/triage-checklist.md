# Triage Checklist

Use this before editing code when the report is vague or mixes frontend, Rust, and security symptoms.

## 1. Confirm the real surface

- Run `tauri info`.
- Confirm the frontend package manager and lockfile.
- Confirm whether the issue happens in `tauri dev`, `tauri build`, `tauri android dev`, or `tauri ios dev`.
- Confirm whether the failing feature is desktop-only, mobile-only, or shared.

## 2. Open the right files first

- `src-tauri/src/lib.rs`
- `src-tauri/src/main.rs`
- `src-tauri/tauri.conf.json`
- `src-tauri/capabilities/*.json`
- `src-tauri/permissions/*.toml`
- `src-tauri/Cargo.toml`
- Frontend file that calls `invoke`, `listen`, or a plugin guest package

## 3. Ask the shortest useful question

- Is the failure a compile error, runtime error, permission denial, or packaging failure?
- Is the feature using a plain command, a plugin API, an event, or a channel?
- Which window or webview label is supposed to have access?
- Does the same feature fail on both desktop and mobile?

## 4. Map symptom to root cause candidate

| Symptom | Likely First Root Cause |
| --- | --- |
| `command not found` | Missing `generate_handler!` registration or wrong frontend command name |
| `permission denied` | Missing or mismatched capability entry, or wrong permission ID |
| Command returns `undefined` | Rust function returns nothing, argument keys do not match, or wrong guest import |
| Event listener never fires | Wrong event name, wrong scope, or listener cleanup happened too early |
| Channel never produces messages | Wrong frontend `Channel` wiring or command never received the channel argument |
| Plugin API missing at runtime | Rust plugin not registered or JS guest package not installed/imported |
| Mobile runtime mismatch | Plugin support note ignored, missing native manifest/privacy change, or desktop-only assumption in shared logic |

## 5. Only then change code

- Fix the narrowest root cause first.
- Re-run the exact failing path.
- Broaden verification only after the original path is green.
