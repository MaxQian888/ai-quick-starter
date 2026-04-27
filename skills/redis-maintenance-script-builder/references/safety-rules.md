# Redis Maintenance Safety Rules

## Connection And Credential Rules

- Keep credentials in `REDIS_URL` or the operator's existing secret flow.
- Prefer `rediss://` when TLS is required.
- Do not paste passwords into generated scripts or saved bundle files.

## Keyspace Safety Rules

- Prefer `SCAN` over `KEYS` for operational review on non-trivial datasets.
- Use pattern filters and explicit limits so the first run stays reviewable.
- Sample `TYPE`, `TTL`, and `MEMORY USAGE` before planning cleanup.

## Cleanup Rules

- Default to dry-run.
- Require an explicit execute switch or flag before deletion.
- Prefer `UNLINK` over `DEL` when the deployment supports it, because unlinking reduces synchronous delete pressure.
- Do not generate wildcard flush commands.
- Keep the cleanup pattern narrow enough that an operator can explain key ownership before execution.

## Memory And Latency Rules

- Compare memory findings with `--bigkeys`, `--memkeys`, `MEMORY STATS`, and `SLOWLOG GET`.
- Correlate evictions, expired keys, and connection spikes before changing maxmemory or eviction policy.
- Treat `MEMORY DOCTOR` as advisory evidence, not as automatic authority.

## Verification Rules

- Record which task bundle was generated and which verification commands actually ran.
- State whether the run was read-only, dry-run, or destructive.
- If the environment blocks live access, stop at script generation and report the gap instead of pretending the run happened.
