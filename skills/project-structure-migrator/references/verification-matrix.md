# Verification Matrix

Use this file after each migration batch to choose the right verification width.

## Per-Batch Minimum

- Re-run the command directly impacted by the moved paths.
- If the batch changes imports, also run the closest typecheck or compile step.
- If the batch changes runtime entrypoints, run the narrowest smoke or startup path.

## By Migration Family

### `monorepo`

- package-local tests for moved packages
- workspace-root lint or typecheck after package checks pass
- root install or build verification once manifests settle

### `restructure`

- affected-module tests
- nearest compile or typecheck path
- app-level integration or smoke checks after local green

### `split-merge`

- per-surface checks for each moved app or package
- shared-contract verification for reused libraries or APIs
- final root verification only after surface-level checks pass

## Escalation Rules

- If no CI or root verify command exists, state that explicitly.
- If multiple package managers or task runners appear, prefer the one backed by lockfiles or CI evidence.
- If validation evidence is weak, keep the claim narrow.
