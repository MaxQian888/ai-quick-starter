# Grader

Evaluate vision-analysis skill responses for accuracy, completeness, and appropriate mode selection.

## Grading Criteria

1. **Mode Selection** — Did the skill choose the correct analysis mode (describe, ocr, ui-review, chart-data, object-detect)?
2. **Prompt Quality** — Is the mode-specific prompt complete and aligned with the analysis goal?
3. **Output Structure** — Does the response follow the expected format for the chosen mode?
4. **Setup Guidance** — If MCP is not configured, does the skill provide correct environment-specific setup instructions?

## Scoring

- **Pass**: Correct mode, complete prompt, proper output format, and accurate setup guidance when needed.
- **Fail**: Wrong mode, incomplete prompt, missing output structure, or incorrect setup instructions.
