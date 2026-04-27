---
name: integrating-redis-into-existing-projects
description: |
  Use this skill whenever you need to integrate Redis into an existing project as a cache, session store, job queue, or rate limiter.
  Make sure to use this skill whenever the user mentions Redis, caching, session store, job queue, bullmq, ioredis,
  redis-py, celery, sidekiq, or adding a cache layer to an app. Also trigger for requests like "add Redis caching",
  "use Redis for sessions", "set up a Redis queue", "cache API responses", "rate limit with Redis",
  or "integrate Redis into my Node/Python/Go/Spring app". Covers cache, session, queue, and rate-limit roles
  across Node.js, Python, Go, Java/Spring, and Ruby projects. Always discover existing seams before adding new ones.
---

# Redis Integration In Existing Projects

## Overview

Integrate Redis by first discovering the repository's real seams, runtime boundaries, and deployment signals.

Prefer adapting the current cache, session, queue, or rate-limit surface over scattering raw Redis calls across handlers, controllers, or jobs.

## Adaptive Detection

Before proposing Redis integration, detect the project shape:

1. **Language and framework**: look for `package.json` (Node/Express/Nest/Next), `pyproject.toml` or `requirements.txt` (Python/Django/FastAPI/Flask), `go.mod` (Go), `pom.xml`/`build.gradle` (Java/Spring), or `Gemfile` (Ruby/Rails).
2. **Existing Redis usage**: search for `redis`, `ioredis`, `bullmq`, `celery`, `sidekiq`, `spring-data-redis`, `connect-redis` in dependencies and source files.
3. **Existing abstractions**: check if the project already has a cache service, session middleware, or queue worker.
4. **Config patterns**: look for `REDIS_URL`, `REDIS_HOST`, or similar environment variables in `.env` files and config modules.
5. **Deployment context**: check for Docker Compose, Kubernetes, or cloud platform signals that affect Redis connectivity.

## Workflow

1. Inspect the existing stack before adding packages.
   - Run `uv run --python 3.11 <skill>/scripts/discover_redis_surface.py --project-root <repo> --json`.
   - Read the detected stacks, frameworks, Redis-related dependencies, config files, and integration candidates.
   - If the repository already has a Redis-backed library such as `bullmq`, `connect-redis`, `celery`, or Spring Data Redis, treat that seam as primary evidence.
2. Choose the Redis role before proposing implementation.
   - `cache`: shared cache service, framework cache layer, or adapter seam.
   - `session`: existing session middleware or server-side session store.
   - `queue`: worker/runtime seam that already expects Redis.
   - `rate_limit`: gateway, middleware, or shared limiter service.
   - If the request mixes multiple roles, scope them explicitly and implement one path at a time.
3. Place connection management in one shared seam.
   - Create or reuse one client factory, provider, or infrastructure module.
   - Keep serialization, timeouts, retry policy, and health checks near that seam.
   - Reuse queue/session framework connection hooks when they exist instead of creating extra ad-hoc clients.
4. Wire configuration and failure modes before broad rollout.
   - Add `REDIS_URL` or the repository's equivalent env/config shape.
   - Define TTL, namespacing, key ownership, and invalidation behavior.
   - Decide what happens when Redis is unavailable: fail closed, fail open, or degrade gracefully.
5. Verify the narrowest affected path first.
   - Start with a failing test or a targeted reproduction for the exact seam you changed.
   - Re-run the seam-level test, then the next broader runtime or integration check.
   - Report what was verified and what remains unverified.

## Guardrails

- Do not introduce a second cache, session, or queue abstraction if the project already has one.
- Do not create Redis clients inside request handlers, controllers, route modules, or job bodies.
- Do not mix multiple Redis client libraries unless the repository already depends on that split and there is a clear reason to keep it.
- Do not treat Redis as a primary database or persistence rewrite unless the user explicitly asks for that architecture change.
- Do not hide missing config, missing health checks, serialization risk, or TTL assumptions.
- Do not claim the integration is complete without verifying startup behavior and at least one failure path or fallback path.
- If the helper script finds no clear seam, stop and report the ambiguity rather than inventing a new architecture.

## References

- Read `references/stack-discovery.md` when you need the exact repo-reading sequence or how to interpret the helper output.
- Read `references/integration-patterns.md` when you need role-specific guidance for cache, session, queue, or rate-limit use cases.
- Read `references/framework-notes.md` when the repository is Node, Python, Spring, or Go and you need a stack-specific seam recommendation.

## Examples

**Add Redis caching to an Express app:**
```powershell
uv run --python 3.11 scripts/discover_redis_surface.py --project-root . --json
# If no existing cache seam, create a shared Redis client factory in src/lib/redis.ts
# Wire it into the API middleware with TTL and graceful degradation.
```

**Use Redis for session storage in a Node.js app:**
```powershell
uv run --python 3.11 scripts/discover_redis_surface.py --project-root . --json
# If connect-redis is already a dependency, reuse it.
# Configure session middleware with the existing Redis client.
```

## Helper Script

Run:

```powershell
uv run --python 3.11 scripts/discover_redis_surface.py --project-root <repo> --json
```

Use the JSON output to decide:

- whether the repo already has Redis-related dependencies,
- which seam is the safest insertion point,
- whether config is already wired,
- and which risks must be called out before any code change.
