# Official Rust Lint Workflow

Use this reference when the Rust lint repair path becomes uncertain or when you need to verify current command behavior against primary sources.

## Primary Sources

- Cargo `cargo fmt`: `https://doc.rust-lang.org/cargo/commands/cargo-fmt.html`
- Cargo `cargo clippy`: `https://doc.rust-lang.org/cargo/commands/cargo-clippy.html`
- Cargo `cargo test`: `https://doc.rust-lang.org/cargo/commands/cargo-test.html`
- Clippy introduction: `https://doc.rust-lang.org/clippy/`
- Clippy usage: `https://doc.rust-lang.org/nightly/clippy/usage.html`
- Clippy installation: `https://doc.rust-lang.org/nightly/clippy/installation.html`

## Key Guidance

### `cargo fmt`

- `cargo fmt` is exposed as an external Cargo subcommand.
- The Cargo docs call out that `cargo fmt` may require an additional optional component.
- Prefer `cargo fmt --all --check` for CI-style verification.

### `cargo clippy`

- `cargo clippy` is also an external Cargo subcommand.
- Clippy's usage guide treats `cargo clippy` as the standard entrypoint.
- Use `cargo clippy -- -D warnings` when warnings must fail the build.
- The Clippy docs note that `-D warnings` also turns ordinary rustc warnings such as `dead_code` into failures.
- Clippy's default lint group is `clippy::all`.
- Do not enable the full `clippy::restriction` group by default; the official docs explicitly warn against enabling that whole group wholesale.

### `cargo test`

- `cargo test` runs unit, integration, and documentation tests unless the manifest disables some targets.
- Arguments after `--` go to the test binary rather than Cargo.
- The Cargo docs note that the working directory for unit and integration tests is the package root, which matters when lint fixes also touch tests or fixture paths.

## Workspace Scoping

- When the selected manifest is a workspace root, default member selection depends on that workspace configuration.
- For a single package inside a workspace, prefer package-level scoping first.
- Clippy's official usage guide documents package selection such as `cargo clippy -p example`.
- The same guide notes that `--no-deps` is available when you truly need to lint only the selected package.

## Installation Notes

- Clippy's installation guide says it is usually already installed with rustup-managed toolchains.
- If the toolchain was installed with the minimal profile, Clippy may be missing.
- The official installation command is `rustup component add clippy [--toolchain=<name>]`.
- Treat missing `rustfmt` or `clippy` components as environment blockers, not code failures.

## Repair Heuristics That Still Need Judgment

- Official docs tell you how commands behave, not whether unused code should be deleted.
- When a lint fix suggests deleting code, trace:
  - registration,
  - exports,
  - feature flags,
  - command handlers,
  - tests,
  before removing it.
- When a framework-specific API is involved, check that framework's official docs next.
