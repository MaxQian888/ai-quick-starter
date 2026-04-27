# Workflow Mapping

Treat `.github/workflows/*.yml` and `.yaml` as the primary source of local CI intent.

Interpret steps like this:
- `run:` steps are the main fallback candidates.
- `actions/checkout` and common setup or cache actions are support steps, not proof that a check passed.
- Unknown or private `uses:` steps must be surfaced as skipped or blocking; do not silently ignore them.

Use these heuristics:
- Validation signals: `test`, `pytest`, `unittest`, `lint`, `ruff`, `mypy`, `pyright`, `typecheck`, `check`, `verify`, `build`, `compile`.
- Deploy signals: `deploy`, `release`, `publish`, `ship` in workflow names, job names, or `run:` commands.
- A workflow that only shows deploy signals should be treated as unsupported for local verification in version one.

When the workflow uses multiple jobs, target the smallest relevant workflow or job first with `--workflow` and `--job`.
