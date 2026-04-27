# Output Contract

## JSON Fields

- `skill_name`: target skill directory name.
- `skill_path`: resolved target path.
- `overall_status`: `clean`, `review-needed`, or `high-risk`.
- `risk_score`: aggregate static risk score from `0` to `100`.
- `summary`: scanned-file count plus category and severity counts.
- `findings`: list of `{category, severity, path, evidence, rationale, suggested_fix}`.
- `safe_fix_plan`: conservative next actions derived from findings.
- `blocked_actions`: actions that should remain off-limits until related findings are fixed.
- `blind_spots`: static-analysis limitations that remain true even when no finding fires.
- `limits`: scan caps or truncation notices.

## Markdown Sections

The Markdown output should always include:

- `## Request`
- `## Overall Status`
- `## Findings`
- `## Safe Fix Plan`
- `## Blocked Actions`
- `## Blind Spots`

## Status Meaning

- `clean`: no supported rule fired in this pass.
- `review-needed`: only medium or low findings were detected.
- `high-risk`: at least one high or critical finding was detected.

## `safe_fix_plan` Meaning

- It is the maximum recommended next edit scope from this audit pass.
- It does not authorize unrelated cleanup.
- Re-run the audit after every applied step.

## `blocked_actions` Meaning

- These are hard-stop actions for the current finding set.
- If a blocked action conflicts with a planned workflow, fix the finding first.

## `blind_spots` Meaning

- They explain what static analysis did not or could not prove.
- A clean report does not override these limits.
