# Business Query Patterns

Use this reference when the user asks for product, growth, audit, or reporting SQL rather than a purely technical syntax conversion.

## Query Framing Checklist

Before finalizing business SQL, make these items explicit when they matter:

- result grain: row-level, user-level, order-level, day-level, week-level, or month-level
- dedup rule: `COUNT(*)`, `COUNT(DISTINCT user_id)`, latest-per-user, or first-event-only
- tenant scope: whether `tenant_id = $1` or a similar tenant filter is required
- soft-delete rule: whether rows with `deleted_at IS NOT NULL` should be excluded
- time window: exact lower and upper bound columns and timezone assumption

## Multi-Tenant Base Filter

```sql
SELECT
  o.id,
  o.status,
  o.total_amount,
  o.created_at
FROM public.orders AS o
WHERE o.tenant_id = $1
  AND o.deleted_at IS NULL
ORDER BY o.created_at DESC;
```

## Daily Active Users

```sql
SELECT
  date_trunc('day', e.created_at) AS day_bucket,
  COUNT(DISTINCT e.user_id) AS daily_active_users
FROM public.user_events AS e
WHERE e.tenant_id = $1
  AND e.deleted_at IS NULL
  AND e.created_at >= $2
  AND e.created_at < $3
GROUP BY 1
ORDER BY 1;
```

## Paid Orders By Day

```sql
SELECT
  date_trunc('day', o.created_at) AS day_bucket,
  COUNT(*) AS paid_orders,
  SUM(o.total_amount) AS paid_revenue
FROM public.orders AS o
WHERE o.tenant_id = $1
  AND o.deleted_at IS NULL
  AND o.status = 'paid'
  AND o.created_at >= $2
  AND o.created_at < $3
GROUP BY 1
ORDER BY 1;
```

## Audit Log Query

```sql
SELECT
  a.id,
  a.actor_user_id,
  a.action,
  a.target_type,
  a.target_id,
  a.created_at
FROM public.audit_logs AS a
WHERE a.tenant_id = $1
  AND a.created_at >= $2
  AND a.created_at < $3
ORDER BY a.created_at DESC
LIMIT $4;
```

## Latest Record Per Entity

```sql
SELECT DISTINCT ON (e.user_id)
  e.user_id,
  e.event_type,
  e.created_at
FROM public.user_events AS e
WHERE e.tenant_id = $1
  AND e.deleted_at IS NULL
ORDER BY e.user_id, e.created_at DESC;
```

## Common Mistakes

- mixing event grain with user grain without saying so
- forgetting `tenant_id` on shared tables
- forgetting `deleted_at IS NULL` on soft-delete tables
- counting raw rows when the metric needs distinct users or distinct orders
- leaving the reporting timezone implicit
