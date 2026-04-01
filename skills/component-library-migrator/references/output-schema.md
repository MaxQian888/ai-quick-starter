# Output Schema

## JSON

- `root`
- `target`
- `mode`
  - `auto-edit`
  - `audit-only`
- `target_library`
  - `requested_name`
  - `canonical_name`
  - `display_name`
  - `is_builtin`
  - `notes`
- `detected_ui_libraries`
- `summary`
  - `component_count`
  - `status_counts`
- `component_findings`
  - `path`
  - `status`
    - `safe-candidate`
    - `blocked`
    - `audit-only`
    - `no-candidate`
  - `native_components`
  - `custom_wrappers`
  - `notes`
- `candidate_mappings`
  - `path`
  - `source_component`
  - `target_component`
  - `confidence`
  - `rationale`
- `safe_fix_plan`
  - `path`
  - `operation`
  - `target_component`
  - `confidence`
  - `rationale`
- `blocked_reasons`
- `forbidden_actions`
- `limits`
- `blind_spots`
- `suggested_next_reads`

## Markdown

Required sections:

1. `## Request`
2. `## Target Library`
3. `## Component Findings`
4. `## Candidate Mappings`
5. `## Safe Fix Plan`
6. `## Forbidden Actions`
7. `## Blocked Reasons`
