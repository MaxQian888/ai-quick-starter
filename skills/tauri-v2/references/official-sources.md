# Official Sources

Last verified with live web lookup on 2026-03-17.

Use these pages before trusting old snippets, third-party tutorials, or cached memory:

| Topic | Official Page | Use It For |
| --- | --- | --- |
| Commands, `invoke`, async restrictions, custom error serialization | `https://tauri.app/develop/calling-rust/` | Confirm command signatures, `generate_handler!`, camelCase argument mapping, `Result<T, E>`, and async argument constraints |
| Events, channels, frontend listeners | `https://tauri.app/develop/calling-frontend/` | Decide between events and channels, check `listen` / `once` / `unlisten`, and verify channel payload shape |
| Capability schema | `https://tauri.app/reference/acl/capability/` | Confirm capability file fields such as `identifier`, `windows`, `webviews`, `permissions`, `remote`, and `platforms` |
| Permission schema | `https://tauri.app/reference/acl/permission/` | Confirm what a permission file can express for app-defined ACL |
| CLI reference | `https://tauri.app/reference/cli/` | Confirm `tauri info`, `tauri add`, `tauri permission ls`, `tauri permission add`, `tauri capability new`, and build/dev flags |
| Dialog plugin | `https://tauri.app/plugin/dialog/` | Confirm setup flow, mobile caveats, and dialog permission names |
| File System plugin | `https://tauri.app/plugin/file-system/` | Confirm plugin setup, base-directory model, mobile caveats, and fs permission patterns |
| Shell plugin | `https://tauri.app/plugin/shell/` | Confirm shell setup, the current `shell` versus `opener` split, platform limits, and execute/open permission shape |

## What changed relative to many older examples

- Current docs use `tauri.app`, not the old `v2.tauri.app` host.
- Current command calls use `@tauri-apps/api/core`.
- Current plugin setup strongly prefers `tauri add <plugin>`.
- Current capability guidance centers on capability files and permission IDs, not on copying ad-hoc config fragments from old posts.

## When to stop and re-open the docs

- A snippet mentions `@tauri-apps/api/tauri`.
- A snippet assumes event payloads are good for high-throughput streams.
- A snippet hardcodes wide-open plugin permissions without scoping.
- A plugin example ignores Android or iOS support notes.
- A repo uses a config or permission pattern you cannot find in the current docs.
