# Stack Discovery

Use this sequence before editing code:

1. Inspect manifests.
   - `package.json`, `pyproject.toml`, `pom.xml`, and `go.mod` tell you which runtime owns the integration.
   - Existing Redis-related dependencies are stronger signals than general framework guesses.
2. Inspect config files.
   - Look for `.env*`, `application.yml`, compose files, and any existing `REDIS_*` keys.
   - If Redis config is absent, surface that gap early instead of coding around it.
3. Inspect the seam candidates.
   - `cache`: shared cache service, cache manager, or framework cache adapter.
   - `session`: session middleware, auth/session store, or server session config.
   - `queue`: worker bootstrap, queue factory, or job runner.
   - `rate_limit`: middleware, gateway, or shared limiter.
4. Inspect tests and existing validation.
   - Prefer changing a seam that already has tests or reproducible runtime behavior.
   - If there is no protection, add the smallest seam-level test first.

## Helper Output

`discover_redis_surface.py` returns:

- `stacks`: coarse runtime families like `node`, `python`, `java`, and `go`.
- `frameworks`: strong framework signals like `nextjs`, `express`, `fastapi`, or `spring`.
- `redis_dependencies`: Redis-capable packages already present, with a `role`.
- `config_files`: files that already mention Redis.
- `integration_candidates`: likely cache/session/queue/rate-limit seams.
- `risks`: ambiguity or drift you must surface.
- `recommendations`: default integration posture for the detected shape.

## Reading Rules

- Prefer an existing framework adapter over a raw client.
- Prefer an existing infrastructure seam over a new utility dropped into application code.
- If two seams compete, choose the one with clearer ownership and verification coverage.
