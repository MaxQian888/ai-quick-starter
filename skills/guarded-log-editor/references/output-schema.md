# Output Schema

## JSON

- `selected_system`
  - `name`
  - `score`
  - `confidence`
  - `notes`
  - `evidence`
- `detected_systems`
  - ranked framework candidates with `name`, `score`, `file_count`, and `evidence`
- `summary`
  - `file_count`
  - `status_counts`
  - `level_totals`
- `file_findings`
  - `path`
  - `status`
  - `frameworks`
  - `dominant_framework`
  - `call_count`
  - `density_per_100_lines`
  - `needs_review`
  - `notes`
- `safe_fix_plan`
  - `path`
  - `operation`
  - `confidence`
  - `rationale`
- `forbidden_actions`
- `blind_spots`
- `suggested_next_reads`
- `recommendations`

## Text Report

Required sections:

1. `## Request`
2. `## Detected Logging System`
3. `## File Findings`
4. `## Safe Fix Plan`
5. `## Forbidden Actions`
6. `## Blind Spots`
7. `## Suggested Next Reads`
