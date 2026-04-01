# Framework Notes

## Node And TypeScript

- `nextjs`: keep Redis access out of random route modules; prefer a shared server-side adapter or infrastructure module.
- `express`: if `express-session` exists, prefer `connect-redis` or the established store seam over replacing session middleware.
- `nestjs`: keep client creation in a provider/module boundary; reuse cache or queue modules when present.
- `bull` or `bullmq`: reuse the queue connection seam instead of instantiating raw clients in producers and processors.

## Python

- `fastapi`: keep Redis access in dependencies, services, or a shared infrastructure module, not inline in every route.
- `django`: prefer `django-redis` or the framework cache/session adapters before raw client calls in views.
- `celery`: treat Celery's broker/backend settings as the main Redis seam; do not create unrelated worker-local clients unless needed.

## Spring

- `spring-boot-starter-data-redis`: prefer configuration through Spring beans and `application.yml` rather than manual client wiring scattered across services.
- `spring-session-data-redis`: keep session storage on the Spring Session seam.
- If `@EnableCaching` already exists, extend that caching seam instead of adding parallel cache utilities.

## Go

- `go-redis`: create one shared client or interface in infrastructure code and inject it into handlers/services.
- `asynq`: reuse the queue client/server lifecycle seam instead of separate ad-hoc Redis clients.

## Escalation Rule

If the repository already has an internal platform module for caching, sessions, jobs, or rate limiting, follow that seam first even if a framework-specific shortcut also exists.
