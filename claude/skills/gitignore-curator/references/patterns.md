# Pattern Guidance

## Safe Defaults

These paths are usually safe to ignore when they are present in the repository, not already covered, and not currently tracked by git:

- Node and frontend build artifacts: `node_modules/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`, `dist/`, `build/`
- Python local artifacts: `.venv/`, `venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.tox/`, `.nox/`, `htmlcov/`
- Workspace tool caches and scratch output: `.uv-cache*/`, `.uv-python/`, `.tmp-tests/`, `tmp/`
- Observed scratch directories with temporary naming: `_tmp*/` only when those directories actually exist
- Tooling and editor metadata: `.idea/`, `.vs/`, `.terraform/`, `.gradle/`
- Local environment files: `.env`, `.env.local`, `.env.<name>.local`
- OS or log noise: `.DS_Store`, `Thumbs.db`, `*.log`
- Editor swap files: `*.swp`, `*.swo` (route to `.git/info/exclude` since they are per-checkout)

## Target File Routing

- `.gitignore`: shared generated artifacts, caches, local env files, and other rules that should travel with the repository.
- `.git/info/exclude`: editor metadata and machine-local OS noise that should stay local to one checkout.
- Non-git workspace: route everything to `.gitignore` because `.git/info/exclude` is unavailable.
- `.dockerignore`: generated directories that do not belong in Docker build contexts, but only when Docker is clearly in play.
- `.eslintignore`, `.prettierignore`, `.ignore`: generated output that those tools should skip, but only when those ignore files already exist or the repo clearly uses them.
- `.npmignore`: inspect carefully. Publishing filters are higher risk than VCS ignore rules, so do not auto-add there without explicit user intent.

## Use Conservative Evidence

Prefer patterns that are supported by at least one of:

1. a clear stack signal such as `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, or Docker files
2. an observed generated directory or file in the working tree
3. `git status` showing untracked or modified generated artifacts
4. recent commits that help explain current churn or existing ignore-file conventions

In non-git workspaces, lean on observed directories, file names, and stack signals. Recent commit history is supporting evidence, not a standalone license to ignore a path. If the evidence is weak, leave the item for human review instead of auto-adding it.

## Never Hide Tracked Content

- If `git ls-files` already contains paths matching a candidate pattern, skip that rule and surface the conflict.
- Treat intentionally tracked build outputs, vendored directories, generated docs, or checked-in examples as human-review territory.

## Never Auto-Add

Do not add rules for directories or files that often contain source or committed assets:

- `src/`, `app/`, `lib/`, `public/`, `docs/`, `scripts/`
- `migrations/`, `fixtures/`, `examples/`, `sample-data/`
- deployment or infrastructure manifests
- product configuration files
- template files such as `.env.example` or `.env.sample`

## Apply Strategy

- Reuse the existing ignore-file structure.
- Prefer appending a short marked section instead of rewriting whole files.
- Skip any pattern that is already present in the target ignore file.
- If the user explicitly asked for direct cleanup, analyze first and then apply without a separate confirmation round.
- If a proposed pattern would hide work-in-progress or already-tracked source content, drop it and report the ambiguity instead.
