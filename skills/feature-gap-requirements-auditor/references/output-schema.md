# Output Schema

## JSON

- `request`
  - `root`
  - `target`
  - `target_mode`
  - `explicit_docs`
  - `include_contract_requirements`
- `discovered_docs`
  - `path`
  - `kind`
  - `role`
  - `extract_requirements`
- `doc_requirements`
  - `id`
  - `path`
  - `section`
  - `text`
  - `keywords`
  - `priority`
  - `category`
  - `source_role`
- `target_summary`
  - `file_count`
  - `kind_counts`
- `target_files`
  - `path`
  - `kind`
  - `identifiers`
- `feature_gap_candidates`
  - `requirement_id`
  - `requirement_text`
  - `path`
  - `section`
  - `category`
  - `priority`
  - `status`
  - `keywords`
  - `matched_source_keywords`
  - `matched_test_keywords`
  - `related_files`
- `guardrail_findings`
  - same shape as `feature_gap_candidates`
- `detailed_requirements`
  - `title`
  - `status`
  - `priority`
  - `rationale`
  - `evidence`
  - `related_files`
  - `acceptance_criteria`
  - `open_questions`
- `blind_spots`
- `suggested_next_reads`
- `limits`

## Markdown

Required sections:

1. `## Request`
2. `## Documentation Signals`
3. `## Target Surface`
4. `## Gap Candidates`
5. `## Guardrail Findings`
6. `## Detailed Requirements`
7. `## Blind Spots`
8. `## Suggested Next Reads`
