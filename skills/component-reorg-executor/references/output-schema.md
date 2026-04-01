# Output Schema

`scripts/apply_component_reorg_plan.py` emits both JSON and Markdown.

## JSON Fields

- `plan_path`: absolute path to the input planner JSON
- `root`: absolute repository root
- `target_directory`: target directory relative to root
- `summary`
  - `moved`
  - `rewritten_files`
  - `skipped_entries`
- `applied_moves`: executed file moves
- `rewritten_files`: relative paths of files whose imports or exports changed
- `skipped_entries`: planner entries that were not executed

## Applied Move Entry

- `source_path`
- `destination_path`
- `proposed_subfolder`

## Markdown Sections

- `## Request`
- `## Applied Moves`
- `## Rewritten Files`
- `## Skipped Entries`
