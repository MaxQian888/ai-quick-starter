# Tests

This directory contains test cases for the tauri-v2 skill.

## Test Cases

1. **Command registration** — Verify `#[tauri::command]` functions are registered in `generate_handler!`.
2. **Permission wiring** — Confirm capability files match window labels and permission IDs.
3. **Plugin setup** — Validate three-part plugin changes (Rust crate, guest JS, ACL scaffolding).
4. **Config validation** — Ensure `build.devUrl` and `build.frontendDist` match frontend output.

Add tests here as the skill evolves.
