# Command Discovery

Use `scripts/discover_build_surface.py` before choosing commands.

Source-of-truth order:
1. GitHub Actions `run:` steps that clearly represent local validation.
2. Make targets or other task-runner entrypoints.
3. Manifest scripts such as `package.json` scripts.
4. Tool configuration inferred from files such as `pyproject.toml` or `Cargo.toml`.
5. Generic ecosystem defaults only when higher-confidence signals are missing.

Package-manager rules:
- `pnpm-lock.yaml` or `packageManager: pnpm@...` -> prefer `pnpm`.
- `package-lock.json` -> prefer `npm`.
- `yarn.lock` -> prefer `yarn`.
- `bun.lockb` or `bun.lock` -> prefer `bun`.
- `uv.lock` -> prefer `uv`.
- `poetry.lock` -> prefer `poetry`.

Classification rules:
- `install`: dependency bootstrap commands.
- `build`: compile or bundle commands.
- `test`: unit, integration, or verification commands that exercise behavior.
- `lint`: style or static rule enforcement.
- `typecheck`: type-system validation.
- `verify`: broader aggregate checks such as `make check`, `cargo check`, or CI wrappers.

Monorepo handling:
- Treat `workspaces`, `pnpm-workspace.yaml`, `turbo.json`, and `nx.json` as monorepo signals.
- Narrow to the affected package before broad validation.
- Do not assume the root command is safe for every change if the repository structure suggests package-level ownership.

If CI commands and local scripts disagree, prefer the command with the clearest evidence and state the uncertainty explicitly.
