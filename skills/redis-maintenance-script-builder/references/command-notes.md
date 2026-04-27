# Redis Command Notes

## Official CLI Notes

- `redis-cli --scan` uses the SCAN family and can combine with `--pattern` to filter keys.
- `redis-cli -i <seconds> --scan` adds pacing between SCAN calls when the server is busy.
- `redis-cli --bigkeys` and `redis-cli --memkeys` are useful for finding large memory footprints before cleanup.
- `SLOWLOG GET` is the first stop for server-side slow command evidence.
- `LATENCY LATEST` can expose the latest latency events when the server supports latency monitoring.
- `MEMORY STATS` gives a compact memory overview; `MEMORY DOCTOR` is a heuristic advisory layer.
- `CLIENT LIST` provides a point-in-time client snapshot; `CLIENT INFO` can expose information about the current connection on newer servers.

These notes are aligned with the current official Redis docs and CLI guidance. Keep them as guidance, not as a substitute for the live server's command support.

## Command Choice Heuristics

- Prefer `PING`, `INFO`, `SLOWLOG`, `LATENCY`, `CLIENT`, `SCAN`, `TYPE`, `TTL`, and `MEMORY USAGE` for first-pass diagnostics.
- Avoid `KEYS` on large datasets.
- Avoid `SAVE` on busy primaries unless the user's runtime and persistence model clearly allow it.
- Prefer `UNLINK` for generated cleanup scripts so deletion work can be offloaded asynchronously.

## redis-py Notes

- `redis.from_url(...)` supports `redis://`, `rediss://`, and `unix://` schemes.
- `decode_responses=True` is helpful when the script should emit readable JSON rather than byte strings.
- `health_check_interval=2` is a reasonable default for maintenance helpers that may stay connected briefly.
- `scan_iter()` is the natural redis-py equivalent of SCAN-based key iteration.
- `info(section="memory")`, `memory_stats()`, `memory_usage(key)`, and `slowlog_get()` cover the common maintenance reads used in this skill.
- Use a non-transactional pipeline when cleanup must batch `UNLINK` calls without requiring atomicity.
