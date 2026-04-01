---
name: postgres-sql-writer
description: Use when Codex needs to write, rewrite, explain, parameterize, or review PostgreSQL SQL, DDL, DML, EXPLAIN plans, or light index advice; translate natural-language data requirements into PostgreSQL queries; or draft editable placeholder SQL when table or column names are incomplete or unknown.
---

# PostgreSQL SQL Writer

Use this skill for PostgreSQL authoring and review tasks, not for running SQL against a live database. Default to a useful first draft even when the schema is incomplete, and keep `EXPLAIN` or index advice lightweight unless the user explicitly asks for deep tuning.

## Workflow

1. Extract the real request shape first: operation, tables, filters, joins, grouping, sorting, pagination, mutations, expected output columns, and result grain.
2. If the schema is missing or partial, state only the minimum assumptions needed to write SQL and use editable placeholders in `snake_case`.
3. Write PostgreSQL SQL, not generic cross-database SQL. Prefer PostgreSQL features only when they simplify the answer or improve correctness.
4. Explain how to adapt the placeholders to the user's real schema.
5. Add concise safety notes when the query can accidentally become destructive, expensive, or semantically wrong.
6. When the user provides `EXPLAIN` or `EXPLAIN ANALYZE`, identify the dominant scan, join, sort, and filter behavior before suggesting a rewrite or index.
7. When the user asks for a business metric, make the grain, dedup rule, tenant scope, soft-delete rule, and time window explicit before finalizing the SQL.

## Default Output Shape

When writing new SQL from incomplete requirements, answer in this order:

1. `Assumptions`
2. `PostgreSQL SQL`
3. `How To Adapt`
4. `Optional Next Refinements`

When explaining or reviewing existing SQL, answer in this order:

1. `What It Does`
2. `Potential Issues`
3. `PostgreSQL Notes`
4. `Suggested Rewrite`

When reviewing an `EXPLAIN` or `EXPLAIN ANALYZE`, answer in this order:

1. `Plan Summary`
2. `Likely Bottleneck`
3. `Index Or Rewrite Suggestions`
4. `Cautions`

## Placeholder Rules

- Use realistic placeholder identifiers such as `public.users`, `orders`, `created_at`, `status`, `tenant_id`, `payload_jsonb`, and `deleted_at`.
- Keep placeholders editable. Do not invent a full schema narrative unless the user asked for schema design.
- Mark assumptions explicitly instead of burying them in prose.
- Use column aliases when they improve readability of aggregates or CTE output.

## Authoring Rules

- Prefer explicit column lists over `SELECT *` unless the user is exploring.
- Prefer parameterized examples with `$1`, `$2`, `$3` when external input is involved.
- Use `RETURNING` for write operations when the caller likely needs inserted or updated rows.
- Use `ON CONFLICT` only when the conflict target is reasonably inferable; otherwise mark it as an assumption.
- Prefer `ILIKE`, `FILTER`, `jsonb_*`, `date_trunc`, and CTEs when they fit naturally in PostgreSQL.
- Keep example SQL formatted and ready to copy.
- If index advice is requested, tie it directly to `WHERE`, `JOIN`, `ORDER BY`, or grouping patterns already visible in the SQL or plan.
- If the request sounds like a business report, state whether the result is at user, order, event, day, week, or month grain.

## Guardrails

- Do not claim placeholder names are real schema truth.
- Do not emit `UPDATE` or `DELETE` without a `WHERE` clause unless the user explicitly requests a full-table operation.
- Call out join keys that are assumed rather than known.
- Mention `NULL` behavior when predicates or aggregates depend on it.
- Mention timezone assumptions when writing timestamp filters.
- Flag when an index may be needed, but keep indexing advice brief unless the user asks for tuning.
- Do not recommend a new index without naming the query pattern it serves.
- Do not treat `EXPLAIN ANALYZE` timing numbers as globally stable; interpret them as workload-specific evidence.

## References

- Read `references/postgres-guardrails.md` when the task involves safety, correctness, joins, null semantics, parameterization, or mutation queries.
- Read `references/query-recipes.md` when the user wants a fast first draft for common PostgreSQL patterns such as aggregates, CTEs, upserts, JSONB filters, pagination, or DDL.
- Read `references/explain-and-index-review.md` when the user wants `EXPLAIN` review, plan interpretation, or index suggestions tied to an existing query.
- Read `references/business-query-patterns.md` when the user asks for analytics, tenant-aware reporting, audit logs, soft-delete-safe queries, or other business-facing SQL.
