# Analysis Playbook

## Command Shapes

Default architecture snapshot:

```bash
python scripts/build_project_architecture_report.py --root <repo>
```

Bias toward one subsystem or feature:

```bash
python scripts/build_project_architecture_report.py --root <repo> --focus "login"
```

Narrow a large repository:

```bash
python scripts/build_project_architecture_report.py --root <repo> --include apps/web --exclude vendor
```

Stable output paths:

```bash
python scripts/build_project_architecture_report.py --root <repo> --markdown-out <report>.md --json-out <report>.json
```

## Narrowing Rules

- Start broad only when the repository is still unfamiliar.
- Add `--focus` when the user names a subsystem, bounded context, feature, or design concern.
- Add `--include` and `--exclude` before opening many extra files in a noisy monorepo.
- Re-run the script after narrowing instead of treating the first pass as permanently sufficient.

## How To Read The Results

1. Read `summary.docs` and `summary.manifests` first.
2. Check `architecture.entry_candidates` and `architecture.top_directories` before opening code.
3. Use `architecture.boundaries` to decide where cross-module coupling actually appears.
4. Treat `architecture.design_patterns` as heuristics backed by observed file shape and imports.
5. Treat `architecture.drift_risks` as review prompts, not automatic defects.
6. Use `linked_skills` and `suggested_next_reads` to choose the next smallest step.

## Answer Framing

- Mark direct file-path, manifest, or import observations as observed.
- Mark pattern names, risk summaries, and skill recommendations as inferred from the observed evidence.
- If a user asks for runtime truth, direct them to a follow-on skill such as `$build-project-fixer` or `$feature-call-chain-mapper`.

## Good Follow-Up Questions

- "Do you want a broader repo map or just this subsystem?"
- "Should I convert this snapshot into root or module docs next?"
- "Do you need runtime verification for the command surface before trusting this design conclusion?"
