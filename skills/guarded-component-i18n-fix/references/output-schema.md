# Output Schema

## JSON

- `selected_system`
  - `name`
  - `kind`
  - `score`
  - `confidence`
  - `notes`
  - `evidence`
- `detected_systems`
  - ranked candidates with `name`, `kind`, `score`, and `evidence`
- `summary`
  - `component_count`
  - `status_counts`
- `component_findings`
  - `path`
  - `status`
  - `uses_translation`
  - `candidate_strings`
  - `notes`
- `safe_fix_plan`
  - `path`
  - `operation`
  - `confidence`
  - `rationale`
- `forbidden_actions`
- `limits`
- `blind_spots`
- `suggested_next_reads`

## Markdown

Required sections:

1. `## Request`
2. `## Detected I18n System`
3. `## Component Findings`
4. `## Safe Fix Plan`
5. `## Forbidden Actions`
6. `## Blind Spots`
7. `## Suggested Next Reads`
