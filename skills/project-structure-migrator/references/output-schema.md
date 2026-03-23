# Output Schema

`build_migration_blueprint.py` emits one Markdown report and one JSON truth source.

## JSON Top-Level Fields

### `project_profile`

- `project_root`
- `git_root`
- `stack`
- `stack_evidence`
- `workspace_files`
- `ci_files`

### `migration_classification`

- `type`
- `confidence`
- `evidence`
- `ambiguities`

### `current_structure`

- `top_level_directories`
- `manifests`
- `workspace_files`
- `ci_files`
- `src_directories`
- `mixed_concerns`
- `coupling_hotspots`

### `target_structure`

- `layout`
- `recommended_patterns`
- `compatibility_strategy`

### `migration_batches`

Each batch should include:

- `id`
- `title`
- `goal`
- `depends_on`
- `primary_paths`
- `verification`

### `verification_plan`

- `per_batch`
- `adjacent`
- `final`

### `risk_register`

List of dictionaries with:

- `severity`
- `title`
- `detail`

### `forbidden_moves`

Flat list of disallowed migration behaviors.

### `open_questions`

Flat list of unresolved decisions or weak-evidence warnings.

## Markdown Sections

The Markdown report should mirror the JSON payload with these headings:

1. `## Project Profile`
2. `## Migration Classification`
3. `## Current Structure`
4. `## Target Structure`
5. `## Migration Batches`
6. `## Verification Plan`
7. `## Risk Register`
8. `## Forbidden Moves`
9. `## Open Questions`
