# PostgreSQL Query Recipes

Use these patterns as editable starting points. Replace placeholder identifiers with the real schema.

## Filtered SELECT

```sql
SELECT
  u.id,
  u.email,
  u.status,
  u.created_at
FROM public.users AS u
WHERE u.status = $1
  AND u.created_at >= $2
ORDER BY u.created_at DESC
LIMIT $3;
```

## Aggregate With `date_trunc`

```sql
SELECT
  date_trunc('day', o.created_at) AS day_bucket,
  COUNT(*) AS order_count,
  SUM(o.total_amount) AS gross_amount
FROM public.orders AS o
WHERE o.created_at >= $1
  AND o.created_at < $2
GROUP BY 1
ORDER BY 1;
```

## `INSERT` With `RETURNING`

```sql
INSERT INTO public.users (
  email,
  status,
  created_at
) VALUES (
  $1,
  $2,
  NOW()
)
RETURNING id, email, status, created_at;
```

## `UPDATE` With Guarded `WHERE`

```sql
UPDATE public.orders
SET status = $1,
    updated_at = NOW()
WHERE id = $2
  AND tenant_id = $3
RETURNING id, status, updated_at;
```

## Upsert With `ON CONFLICT`

```sql
INSERT INTO public.user_settings (
  user_id,
  notify_by_email,
  updated_at
) VALUES (
  $1,
  $2,
  NOW()
)
ON CONFLICT (user_id)
DO UPDATE
SET notify_by_email = EXCLUDED.notify_by_email,
    updated_at = NOW()
RETURNING user_id, notify_by_email, updated_at;
```

## JSONB Filter

```sql
SELECT
  e.id,
  e.event_type,
  e.payload_jsonb
FROM public.events AS e
WHERE e.payload_jsonb ->> 'source' = $1
  AND (e.payload_jsonb -> 'flags') ? $2
ORDER BY e.created_at DESC;
```

## CTE For Ranked Results

```sql
WITH ranked_orders AS (
  SELECT
    o.*,
    ROW_NUMBER() OVER (
      PARTITION BY o.customer_id
      ORDER BY o.created_at DESC
    ) AS row_num
  FROM public.orders AS o
)
SELECT
  customer_id,
  id AS latest_order_id,
  total_amount,
  created_at
FROM ranked_orders
WHERE row_num = 1;
```

## Pagination

```sql
SELECT
  p.id,
  p.title,
  p.published_at
FROM public.posts AS p
WHERE p.published_at IS NOT NULL
ORDER BY p.published_at DESC, p.id DESC
LIMIT $1 OFFSET $2;
```

## Basic DDL

```sql
CREATE TABLE IF NOT EXISTS public.orders (
  id BIGSERIAL PRIMARY KEY,
  tenant_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  status TEXT NOT NULL,
  total_amount NUMERIC(12, 2) NOT NULL,
  payload_jsonb JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_tenant_status_created_at
  ON public.orders (tenant_id, status, created_at DESC);
```
