# IPC Patterns

Use the smallest IPC primitive that matches the data shape and frequency. The official docs split the frontend-to-Rust path and the Rust-to-frontend path, but in practice you should decide from the feature shape first.

## Decision Table

| Need | Primitive | Why |
| --- | --- | --- |
| One request, one response | Command plus `invoke` | Strong typing, straightforward error handling, easiest to test |
| Broadcast or low-volume notifications | Events | Good for simple fan-out and lifecycle signals |
| Ordered streaming or frequent updates | `Channel` | Better fit for progress, logs, child-process output, or any larger stream |

## Commands

Use commands for the normal frontend-to-Rust path.

### Rules

- Define commands with `#[tauri::command]`.
- Register them in `tauri::generate_handler![...]`.
- Use `@tauri-apps/api/core` on the frontend.
- Pass arguments as a JSON object with camelCase keys unless you explicitly change rename behavior.
- Prefer `Result<T, E>` return types for operations that can fail.

### Async constraints

- Async commands run off the main thread and are preferred for heavier work.
- Borrowed arguments such as `&str` are a common footgun in async command signatures; use owned types instead.
- `State<'_, T>` in async commands needs special care. If the shape becomes awkward, refactor the command boundary instead of fighting the type system blindly.

### Error shape

- For simple failures, `Result<T, String>` is enough.
- For stable frontend handling, serialize a custom error enum instead of leaking arbitrary Rust error text.
- For large binary payloads, prefer `tauri::ipc::Response` over normal JSON serialization.

## Events

Use events when Rust needs to notify one or more frontend listeners and the payload volume is small.

### Good fits

- Job started or finished notifications
- Authentication state changes
- Broadcast signals to several windows or webviews
- One-off messages that do not need strong typing at the transport layer

### Constraints

- Event payloads are JSON-based and not ideal for large or high-throughput streams.
- Global events go to all listeners; webview-specific events only go to the targeted webview.
- Frontend listeners must be cleaned up with the returned `unlisten` function when the component scope ends.

### Frontend imports

- Global listeners: `@tauri-apps/api/event`
- Webview-specific listeners: `@tauri-apps/api/webviewWindow`

## Channels

Use channels when the data is ordered, frequent, or long-lived.

### Good fits

- Download or upload progress
- Shell child-process output
- Streaming logs
- Multi-step backend jobs that need incremental UI feedback

### Rules

- Accept `tauri::ipc::Channel<T>` as a command argument.
- Serialize channel messages as explicit structs or tagged enums.
- Create the matching `new Channel<T>()` on the frontend and pass it to `invoke(...)`.
- Keep message names and casing stable if the frontend narrows on a discriminated union.

## End-to-end checklist

1. Prove the feature really needs a stream before choosing events or channels.
2. Define the Rust payload type first.
3. Register the command that owns the IPC flow.
4. Add or confirm any plugin permissions needed by that command.
5. Wire the frontend import from the correct Tauri package.
6. Re-run the exact interaction path after the wiring change.
