# Grader Instructions

## Purpose

Evaluate outputs from the `daily-news-multisource-brief` skill for accuracy, completeness, and source integrity.

## Grading Criteria

1. **Source Attribution** — Every item includes headline, link, source name, and publish time.
2. **Coverage Transparency** — Failed sources are reported; coverage gaps are explicit.
3. **Organization** — Items grouped by region (CN/Global) and topic in correct priority order.
4. **Format Compliance** — Output matches requested format (Markdown/JSON) with correct fields.
5. **Deduplication** — Duplicate stories across sources are identified and consolidated.

## Scoring

- **Pass**: All criteria met; brief is well-organized and fully attributed.
- **Partial**: Minor issues (e.g., missing timestamp on one item, slight ordering inconsistency).
- **Fail**: Major issues (e.g., missing source links, fabricated coverage claims, no failed-source reporting).
