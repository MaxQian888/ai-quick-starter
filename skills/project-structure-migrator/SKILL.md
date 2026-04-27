---
name: project-structure-migrator
description: |
  Use whenever you need to migrate a repository's project structure, such as moving a single project to a workspace or monorepo, reorganizing a legacy directory layout into clearer boundaries, or splitting or merging project surfaces while preserving builds, tests, and entrypoints. Make sure to use this skill whenever the user says "restructure", "reorganize", "move to monorepo", "workspace migration", "split packages", "merge repos", "flat to feature-based", or "clean up directory structure" — even for partial migrations or exploratory restructuring. Also trigger when adding a new package to an existing monorepo, converting a CRA app to a Next.js app within a workspace, or any task that changes file locations and import paths. Covers JavaScript/TypeScript, Python, Rust, Go, and mixed-language repositories.
---

# Project Structure Migrator

## Overview

Analyze a repository's current structure, generate a staged migration blueprint, and execute the migration batch by batch without collapsing structure work, validation, and unrelated rewrites into one risky pass.

Default to structured artifacts: one Markdown blueprint for review and one matching JSON document as the machine-readable truth source.

## Adaptive Detection

Before migrating, detect repository signals:

1. **Current layout**: Check if the repo is flat, layered, feature-based, or already a monorepo.
2. **Manifest files**: Identify `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, and workspace configs.
3. **Workspace tools**: Look for `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, or `Cargo.toml` workspaces.
4. **Import patterns**: Note path aliases, barrel exports, and relative import density.
5. **Validation chain**: Identify build, test, lint, and typecheck commands from manifests and CI.

Use these signals to choose the migration type and compatibility strategy.

## Quick Start

1. Confirm the real `project-root` and nearest git root.
2. Run the blueprint generator before freehand migration advice:

```bash
python scripts/build_migration_blueprint.py --project-root <repo> --output-dir <out-dir>
```

3. Read the JSON output first.
4. Use the Markdown report for review and communication.
5. Execute one migration batch at a time, with verification after each batch.

## Workflow

### 1. Detect Before Deciding

Inspect repository signals first:

- manifests such as `package.json` and `pyproject.toml`,
- workspace files such as `pnpm-workspace.yaml`, `turbo.json`, and `nx.json`,
- CI workflows,
- and the actual top-level and `src/` directory shape.

Do not assume the current directory is the project root. Do not guess the migration type from one file.

### 2. Generate The Migration Blueprint

Run `scripts/build_migration_blueprint.py` and treat the JSON artifact as the truth source.

Use these flags only when the user already fixed the target direction:

- `--migration-type auto|monorepo|restructure|split-merge`
- `--stack auto|js-ts|python|mixed`
- `--target-shape <hint>`
- `--json-out <path>`
- `--markdown-out <path>`

Read [references/output-schema.md](references/output-schema.md) when you need the exact field contract.

### 3. Separate Facts From Recommendations

Treat these as observed repository facts:

- detected manifests,
- detected workspace files,
- detected CI files,
- current concern boundaries,
- and the strongest available validation signals.

Treat these as migration recommendations:

- target layout,
- compatibility strategy,
- migration batch order,
- and final cleanup timing.

If confidence is low, surface `open_questions` instead of flattening uncertainty into false certainty.

### 4. Execute In Batches

Decompose the migration into batches that each do one primary job:

- create target skeleton and compatibility seams,
- move one structural concern at a time,
- then remove legacy paths only after downstream callers migrate.

Every batch must include:

- a narrow verification step,
- a neighboring-impact verification step,
- and a clear dependency edge from earlier batches.

Read [references/migration-types.md](references/migration-types.md) when deciding whether the migration is closer to `monorepo`, `restructure`, or `split-merge`.

### 5. Preserve Compatibility Until The End

When path aliases, import roots, package names, or task-runner entrypoints are likely to change:

- keep compatibility shims,
- keep transitional forwarding files or aliases,
- and only remove them after the downstream surface is migrated and verified.

Do not turn a structure migration into a big-bang cutover unless the repository is tiny and the user explicitly wants that risk.

### 6. Widen Verification Carefully

After each batch:

1. re-run the directly impacted command,
2. run neighboring checks that share the moved paths,
3. then run the strongest repository-native final validation chain you can prove from manifests or CI evidence.

Read [references/verification-matrix.md](references/verification-matrix.md) when choosing how wide to verify for each migration family.

## Guardrails

- Do not start moving directories before discovering the repository's validation commands.
- Do not mix structure migration with unrelated business-logic rewrites in the same batch.
- Do not remove compatibility shims before downstream callers migrate.
- Do not move multiple high-coupling subtrees in one uncontrolled pass.
- Do not claim a migration is complete unless the final verification chain actually ran.

Read [references/execution-guardrails.md](references/execution-guardrails.md) before editing when the migration boundary or risk level is unclear.

## Output Review Checklist

Before acting on the blueprint, confirm:

- `migration_classification.type` matches the repository shape,
- `current_structure` reflects the real hotspots and mixed concerns,
- `target_structure` is plausible for this repository instead of generic boilerplate,
- `migration_batches` keep one primary concern per batch,
- `verification_plan` maps to real commands,
- and `open_questions` is not silently empty when evidence is weak.

## Examples

### Example 1: Generate a migration blueprint

```bash
python scripts/build_migration_blueprint.py --project-root . --output-dir ./migration-plan
```

### Example 2: Targeted monorepo migration with stack hint

```bash
python scripts/build_migration_blueprint.py --project-root . --migration-type monorepo --stack js-ts --output-dir ./migration-plan
```

## References

- Migration taxonomy: [references/migration-types.md](references/migration-types.md)
- Guardrails: [references/execution-guardrails.md](references/execution-guardrails.md)
- Verification policy: [references/verification-matrix.md](references/verification-matrix.md)
- Output contract: [references/output-schema.md](references/output-schema.md)
- Blueprint generator: [scripts/build_migration_blueprint.py](scripts/build_migration_blueprint.py)
