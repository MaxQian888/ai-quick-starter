# EXPLAIN And Index Review

Use this reference when the user provides `EXPLAIN` or `EXPLAIN ANALYZE`, asks why a PostgreSQL query is slow, or wants lightweight index suggestions grounded in the query shape.

## Review Order

1. Identify the most expensive visible operation first.
2. Check whether the plan is dominated by `Seq Scan`, `Index Scan`, `Bitmap Heap Scan`, `Sort`, `Hash Join`, `Merge Join`, or nested loops.
3. Tie every suggestion back to a concrete predicate, join key, or `ORDER BY`.
4. Prefer one or two grounded changes over an index shopping list.

## Plan Summary Language

- `Seq Scan`: the planner is reading most or all rows from a table.
- `Index Scan`: the planner can walk an index in key order and fetch matching rows.
- `Bitmap Heap Scan`: multiple row locations are gathered first, then fetched in batches.
- `Sort`: rows are being reordered after filtering or joining.
- `Hash Join`: one side is hashed in memory and probed by the other side.

## What To Look For

- Filters repeated in `WHERE` clauses.
- Join keys repeated across many queries.
- `ORDER BY` on large result sets.
- Wide scans followed by highly selective filters.
- High row estimates versus actual row counts when `EXPLAIN ANALYZE` is available.

## Index Suggestion Heuristics

- If the query filters by equality on a stable high-selectivity column, consider a B-tree index on that column.
- If the query filters by tenant and then sorts by timestamp, consider a composite index such as `(tenant_id, created_at DESC)`.
- If the query filters by `status` plus time range, consider `(status, created_at)` only when that pattern is frequent enough to justify write overhead.
- If the query only needs a few columns after filtering, mention that an index may still not remove heap access unless it becomes an index-only scan.
- If the query uses JSONB containment or key existence repeatedly, mention JSONB indexing only if the JSON predicate is clearly central.

## Cautions

- `EXPLAIN ANALYZE` includes runtime measurements from a specific workload, cache state, and data distribution.
- Do not recommend every possible index; each index adds write, storage, and maintenance cost.
- Do not treat one slow plan as proof that the SQL itself is wrong; data skew and stale statistics also matter.

## Example Framing

When the user shares a plan, prefer this style:

1. `Plan Summary`: identify the dominant `Seq Scan`, `Index Scan`, join, and sort.
2. `Likely Bottleneck`: say which predicate, join, or ordering is causing most of the work.
3. `Index Or Rewrite Suggestions`: suggest one or two targeted changes.
4. `Cautions`: mention assumptions, write overhead, or missing schema context.
