# Integration Patterns

## Cache

- Best seam: existing cache service, cache manager, or framework cache adapter.
- Store: TTL-bound derived data, request results, and expensive computation outputs.
- Avoid: placing key composition and invalidation logic directly in controllers or route handlers.
- Verify: cache hit, cache miss, invalidation path, and stale-data behavior.

## Session

- Best seam: current session middleware or server-side auth/session store.
- Store: server-side session state, short-lived auth context, or CSRF/session metadata.
- Avoid: replacing the full auth/session stack when only the backing store needs to change.
- Verify: login/session creation, session refresh, logout, and expired-session behavior.

## Queue

- Best seam: existing queue runtime such as BullMQ, Bull, Celery, RQ, Asynq, or an internal worker facade.
- Store: job state, delayed work, retry scheduling, or distributed task handoff.
- Avoid: creating ad-hoc Redis clients inside individual job handlers.
- Verify: enqueue path, worker consumption, retry/failure path, and shutdown behavior.

## Rate Limit

- Best seam: gateway, middleware, or shared request limiter service.
- Store: counters, windows, and lockouts tied to a consistent keying strategy.
- Avoid: sprinkling limit counters across independent handlers with mismatched key schemes.
- Verify: limit exceeded behavior, window reset, and identity/key derivation.

## Shared Decisions

- Define key prefixes and ownership up front.
- Keep serialization format explicit.
- Decide whether failures should fail open or fail closed before rollout.
- Use one shared connection seam unless a framework clearly requires a dedicated integration hook.
