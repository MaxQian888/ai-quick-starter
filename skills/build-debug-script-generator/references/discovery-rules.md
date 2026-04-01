# Discovery Rules

Use repository evidence in this order:

1. root manifest scripts and lockfiles,
2. root `pyproject.toml` and Python lockfiles,
3. `Makefile` targets,
4. GitHub Actions `run:` steps,
5. root entrypoint files.

## Package Manager Priority

### JavaScript

- `pnpm-lock.yaml` -> `pnpm`
- `bun.lockb` or `bun.lock` -> `bun`
- `yarn.lock` -> `yarn`
- `package-lock.json` or bare `package.json` -> `npm`

### Python

- `uv.lock` -> `uv`
- `poetry.lock` -> `poetry`
- bare `pyproject.toml` -> `pip`

## Command Ranking

### Install

- Prefer the package-manager-native install command backed by the detected lockfile.
- Skip install only when no credible manager signal exists.

### Build

Rank build candidates in this order:

1. root `package.json` script such as `build`,
2. root `pyproject.toml` with `[build-system]`,
3. `Makefile` `build` target,
4. CI `run:` command classified as build.

### Quick Debug

Rank quick-debug candidates in this order:

1. root `package.json` script in this order: `dev`, `start:dev`, `debug`, `serve`, `start`,
2. Python entrypoint flows such as `manage.py runserver`, `uvicorn ... --reload`, `python main.py`, `python app.py`,
3. `Makefile` target in this order: `debug`, `dev`, `run`, `start`, `serve`,
4. CI `run:` command only when it clearly represents a dev or debug loop.

### Optional Checks

Select at most one best candidate for each:

- `lint`
- `test`
- `typecheck`

These checks stay optional in `build.ps1` behind `-IncludeChecks`.

## CI Rules

- CI hints can fill missing local buckets.
- CI hints do not outrank explicit root scripts or Make targets.
- CI commands that only prove validation must not be misreported as debug entrypoints.
