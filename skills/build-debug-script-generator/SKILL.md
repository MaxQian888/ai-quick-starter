---
name: build-debug-script-generator
description: >
  Make sure to use this skill whenever the user needs build scripts, debug scripts,
  PowerShell wrappers, or local development automation for an existing repository.
  Also trigger when they mention "how do I build this project," "create a build
  script," "generate debug commands," "local CI scripts," or "repo setup helpers."
  Use it for Node.js, Python, Rust, Go, or mixed projects where manifests, lockfiles,
  CI configs, or Make targets exist. Covers synonyms like "build automation,"
  "dev scripts," "local build helpers," "project bootstrap," "compile wrapper,"
  and "debug workflow." Use it even when the user only says "I want to run this
  project locally" or "how do I compile this."
---

# Build Debug Script Generator

Generate repo-local PowerShell wrappers from repository evidence. Start with the helper script, read the JSON bundle first, then trust or refine the generated scripts based on blockers and assumptions.

## Adaptive Detection

Before generating, detect the project type from repository signals:

- Node.js: `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`
- Python: `pyproject.toml`, `setup.py`, `requirements.txt`, `uv.lock`
- Rust: `Cargo.toml`
- Go: `go.mod`
- CI hints: `.github/workflows/*.yml`, `.gitlab-ci.yml`
- Build tools: `Makefile`, `justfile`, `CMakeLists.txt`
- Entrypoints: `main.py`, `app.py`, `manage.py`, `src/index.ts`

Do not invent a build or debug path before reading those signals.

## Quick Start

1. Confirm the target repository root.
2. Choose an output directory, usually `<repo>/scripts`.
3. Run:

```bash
python scripts/generate_build_debug_scripts.py --project-root <repo> --output-dir <repo>/scripts
```

4. Read `build-debug-bundle.json` before running anything.
5. Review `build.ps1` and `debug.ps1`.
6. If the bundle is credible, run the generated script with the narrowest scope you need.

## Workflow

### 1. Detect Before Generating

Inspect repository truth first:

- `package.json` and lockfiles,
- `pyproject.toml` and Python lockfiles,
- `Makefile`,
- `.github/workflows/*.yml` or `.yaml`,
- root entrypoints such as `main.py`, `app.py`, and `manage.py`.

Do not invent a build or debug path before reading those signals.

### 2. Generate The Bundle

Run the helper script and keep the outputs together:

- `build.ps1`
- `debug.ps1`
- `build-debug-bundle.json`
- `build-debug-bundle.md`

Treat the JSON file as the machine-readable truth source.

### 3. Review Selected Commands

Check these sections first:

- `selected_commands.install`
- `selected_commands.build`
- `selected_commands.debug`
- `optional_checks`
- `blockers`
- `assumptions`

If `blockers` says the debug path is weak or missing, do not pretend the generated `debug.ps1` is trustworthy. Refine the repository context and regenerate.

### 4. Use The Generated Scripts Carefully

`build.ps1` supports:

- `-SkipInstall` to skip dependency bootstrap,
- `-IncludeChecks` to run selected lint, test, or typecheck commands before the primary build step.

`debug.ps1` supports:

- `-SkipInstall` to skip dependency bootstrap.

The scripts fail loudly on command errors. They are wrappers, not orchestration systems.

### 5. Regenerate Instead Of Freehand Guessing

If the repository changes, or if the selected commands are obviously stale, rerun the generator instead of patching the scripts from memory.

## Guardrails

- Do not overwrite an existing hand-maintained script without first reading it and confirming regeneration still matches user intent.
- Do not claim the debug script is valid when the bundle still reports blockers.
- Do not turn quick debug into a full multi-service bootstrap unless the repository already proves that flow.
- Do not add destructive commands, git cleanup, or filesystem rewrites to the generated scripts.
- Do not hide uncertainty. Surface blockers and assumptions exactly as the helper reports them.

## Examples

**Generate for a Node.js repo:**
```bash
python scripts/generate_build_debug_scripts.py --project-root ./my-web-app --output-dir ./my-web-app/scripts
```

**Generate with custom output:**
```bash
python scripts/generate_build_debug_scripts.py --project-root ./backend --output-dir ./backend/.dev-scripts
```

## References

- Read `references/discovery-rules.md` for source-of-truth priority and command ranking.
- Read `references/output-contract.md` for the generated bundle schema and file names.
- Read `references/script-guardrails.md` before editing the helper or widening the generated script behavior.
- Read `scripts/generate_build_debug_scripts.py` for the runtime truth.
