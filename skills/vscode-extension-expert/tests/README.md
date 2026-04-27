# Tests

This directory contains test cases for the vscode-extension-expert skill.

## Test Cases

1. **Command ID parity** — Verify command IDs match across `package.json`, `registerCommand`, and tests.
2. **Webview message contract** — Confirm message types are updated on both sender and receiver.
3. **Template compliance** — Validate required folders, entrypoints, and core scripts are present.
4. **Build and package** — Ensure `pnpm build` and `pnpm package` succeed before release.

Add tests here as the skill evolves.
