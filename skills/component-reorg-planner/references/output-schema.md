# Output Schema

`scripts/build_component_reorg_plan.py` emits both JSON and Markdown.

## JSON Fields

- `root`: absolute repository root
- `target_directory`: target directory relative to root
- `project_context`: output from `detect_component_context.py`
- `summary`:
  - `file_count`
  - `move_candidates`
  - `keep_put`
- `proposed_subfolders`: confident functional buckets with rationale and file list
- `move_plan`: one entry per scanned file
- `blocked_or_keep_put`: subset of `move_plan` that should not move yet
- `risk_register`: follow-up risks for a later execution pass
- `forbidden_moves`: actions the audit explicitly disallows
- `verification_suggestions`: checks for the later execution pass

## Move Plan Entry

- `path`: current relative path
- `file_kind`: `component`, `hook`, `barrel`, `test`, `story`, `style`, `types`, or `other`
- `action`: `move` or `keep-put`
- `proposed_subfolder`: destination bucket when `action=move`
- `destination_path`: proposed future path
- `confidence`: `high`, `medium`, or `low`
- `rationale`: human-readable reason

## Markdown Sections

- `## Request`
- `## Project Context`
- `## Proposed Functional Subfolders`
- `## Move Plan`
- `## Forbidden Moves`
- `## Verification Suggestions`
