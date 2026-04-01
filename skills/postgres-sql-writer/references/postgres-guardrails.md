# PostgreSQL Guardrails

Use this reference when the user asks for a query rewrite, review, mutation statement, or any SQL that could become unsafe or misleading.

## Missing Schema

- State the smallest useful set of assumptions.
- Use editable placeholders such as `public.users`, `created_at`, `status`, `payload_jsonb`.
- Never pretend inferred columns are confirmed.

## Mutation Safety

- Treat `UPDATE` and `DELETE` without `WHERE` as high risk.
- Prefer `RETURNING *` or `RETURNING id, updated_at` when the caller likely needs confirmation.
- If soft delete is plausible, mention `deleted_at` as an adaptation point instead of forcing hard delete.

## Filtering And Parameterization

- Prefer parameter placeholders like `$1`, `$2`, `$3` over string interpolation examples.
- Use `ILIKE` only when case-insensitive matching is intended.
- Use `ANY($1)` for array filters when the caller likely passes multiple values.

## JOIN And NULL Semantics

- Name assumed join keys explicitly.
- Call out when `LEFT JOIN` is safer than `JOIN`.
- Remember `NULL` is not equal to anything, including another `NULL`.
- Use `IS NULL` and `IS NOT NULL`, not `= NULL`.

## Time And Aggregation

- Mention timezone assumptions for date boundaries.
- Prefer `date_trunc(...)` for bucketed aggregation.
- Use `FILTER (WHERE ...)` when conditional aggregates stay readable that way.

## PostgreSQL-Specific Notes

- Prefer `ON CONFLICT` for upserts.
- Prefer `jsonb` operators only when JSON storage is already implied.
- Mention that pagination often needs deterministic `ORDER BY`.
- Suggest indexes only when they directly follow from the query shape, for example filtering by `tenant_id`, `status`, or timestamp ranges.
- When the user shares `EXPLAIN` output, separate observed plan nodes from inferred fixes.
