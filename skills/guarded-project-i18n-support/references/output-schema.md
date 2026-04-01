# Output Schema

## JSON

- `project_profile`
  - `runtimes`
  - `frameworks`
  - `app_shapes`
  - `evidence`
- `selected_system`
  - `name`
  - `kind`
  - `score`
  - `confidence`
  - `notes`
  - `evidence`
- `detected_systems`
  - ranked candidates with `name`, `kind`, `score`, and `evidence`
- `recommended_strategy`
  - `mode`
  - `system`
  - `confidence`
  - `rationale`
- `strategy_options`
  - `system`
  - `fit`
  - `reason`
- `adoption_plan`
  - `step`
  - `action`
  - `rationale`
- `verification_plan`
  - `phase`
  - `check`
- `forbidden_actions`
- `limits`
- `blind_spots`
- `suggested_next_reads`

## Markdown

Required sections:

1. `## Request`
2. `## Project Profile`
3. `## Detected I18n System`
4. `## Recommended Strategy`
5. `## Adoption Plan`
6. `## Verification Plan`
7. `## Forbidden Actions`
8. `## Blind Spots`
9. `## Suggested Next Reads`
