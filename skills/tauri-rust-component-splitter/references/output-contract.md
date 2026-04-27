# Output Contract

`scripts/plan_tauri_rust_split.py` emits both JSON and Markdown.

## JSON Fields

- `root`: absolute repository root
- `target`: target file or directory relative to root
- `project_context`:
  - `tauri_root`
  - `target_kind`
  - `target_relative_path`
  - `nearby_root_files`
- `summary`:
  - `file_count`
  - `symbol_count`
  - `proposed_file_count`
  - `naming_issue_count`
- `naming_findings`: one entry per naming problem
- `proposed_files`: grouped destination files with responsibility and planned symbols
- `symbol_plan`: one entry per detected split-worthy symbol
- `migration_phases`: conservative extraction order
- `scaffold_plan`: the files that would be created with `--scaffold`
- `forbidden_actions`: actions the planner explicitly disallows
- `verification_suggestions`: follow-up checks for the later migration pass
- `scaffold_created`: created files when `--scaffold` runs
- `scaffold_skipped`: pre-existing files the scaffold pass left untouched

## Naming Finding Entry

- `rule`: stable identifier such as `generic-module-name`
- `severity`: `low`, `medium`, or `high`
- `subject`: current file path
- `current_name`: the current module or symbol name
- `suggested_name`: proposed rename when available
- `rationale`: short explanation

## Proposed File Entry

- `path`: proposed destination path relative to root
- `responsibility`: target bucket such as `commands`, `services`, or `state`
- `confidence`: `low`, `medium`, or `high`
- `symbols`: planned symbols for that file
- `rationale`: why the file exists

## Symbol Plan Entry

- `name`: symbol name
- `kind`: `function` or `struct`
- `bucket`: proposed target bucket
- `source_path`: current path
- `line`: approximate source line
- `destination_path`: proposed future file
- `confidence`: confidence in the grouping
- `rationale`: why the symbol was grouped there

## Markdown Sections

- `## Request`
- `## Project Context`
- `## Naming Findings`
- `## Proposed File Layout`
- `## Migration Phases`
- `## Forbidden Actions`
