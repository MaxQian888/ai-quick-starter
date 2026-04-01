# Script Guardrails

Generated scripts may:

- set strict PowerShell execution behavior,
- change into the repository root,
- run the selected install command,
- run optional validation checks,
- run the selected build or quick-debug command,
- and fail loudly on non-zero exit codes.

Generated scripts must not:

- delete files,
- rewrite repository structure,
- reset or clean git state,
- start unrelated background services by guesswork,
- or claim a missing command exists.

## Install Behavior

- Install remains optional at runtime through `-SkipInstall`.
- If no install command was selected, leave the script runnable and surface that gap in the bundle assumptions.

## Validation Behavior

- Keep lint, test, and typecheck optional inside `build.ps1`.
- Do not fold a slow repo-wide suite into `debug.ps1`.

## Regeneration Rule

When repository truth changes:

- rerun the generator,
- re-read the JSON bundle,
- then decide whether a manual script edit is still justified.

Do not patch stale generated scripts from memory when the repository evidence can be refreshed cheaply.
