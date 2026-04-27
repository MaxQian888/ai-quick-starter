# Tauri Boundaries

Use this reference when deciding whether a Rust symbol belongs in a new file or should stay where it is.

## Preferred Split Buckets

| Bucket | Typical contents | Typical destination |
|---|---|---|
| `commands` | `#[tauri::command]` entrypoints and thin request parsing | `src-tauri/src/commands/<context>_commands.rs` |
| `state` | shared app state, `Mutex`/`RwLock` containers, state holders | `src-tauri/src/state/<state_name>.rs` |
| `services` | orchestration logic, background work, repository-like services | `src-tauri/src/services/<service_name>.rs` |
| `platform` | shell, tray, window, clipboard, process, or OS adapters | `src-tauri/src/platform/<adapter_name>.rs` |
| `models` | payloads, DTO-like structs, config records, pure data types | `src-tauri/src/models/<type_name>.rs` |
| `errors` | reusable error enums or error wrappers | `src-tauri/src/errors.rs` or `src-tauri/src/errors/<name>.rs` |

## Boundary Rules

- Keep Tauri commands thin. They should delegate to services or state-aware helpers instead of owning business logic.
- Keep long-lived shared state separate from service orchestration.
- Keep platform adapters isolated from command parsing so platform-specific code does not leak into every entrypoint.
- Keep pure data types away from shell, tray, or window side effects.
- Keep errors reusable and explicit instead of reusing strings everywhere.

## Stop Conditions

- If a symbol has weak or conflicting signals, prefer leaving it in place over forcing a move.
- If the target mixes multiple subsystems with no stable seam, stop at planning and surface the ambiguity.
- If a repository already uses a different but consistent `src-tauri` structure, follow the local convention instead of forcing this reference layout.
- If moving a command would break a public interface contract, keep the signature in place and move only the supporting logic later.
