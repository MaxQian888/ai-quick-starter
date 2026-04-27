---
name: redis-maintenance-script-builder
description: |
  Use whenever you need to maintain an existing Redis deployment, audit memory or slowlog behavior, inspect keyspace patterns, or scaffold safe Redis maintenance scripts in PowerShell, Bash, or Python instead of hand-writing operational commands. Make sure to use this skill whenever the user mentions "Redis", "cache", "memory audit", "slowlog", "keyspace", "Redis cleanup", "eviction", "Redis health", or "Redis maintenance" — even for read-only diagnostics or single-command checks. Also trigger when the user needs to scan keys by pattern, check client connections, review replica status, or generate safe operational scripts for production Redis instances. Covers Redis standalone, Sentinel, and Cluster deployments.
---

# Redis Maintenance Script Builder

## Overview

Generate reviewable Redis maintenance script bundles instead of improvising live commands.

Keep the skill narrow: choose one maintenance task, generate the script and JSON or Markdown bundle, review the safety notes, then run the smallest safe path first.

## Adaptive Detection

Before generating scripts, detect the Redis environment:

1. **Deployment type**: Determine if Redis is standalone, Sentinel, or Cluster.
2. **Shell preference**: Ask or detect if the user prefers PowerShell, Bash, or Python.
3. **Environment**: Note if the target is production, staging, or local development.
4. **Authentication**: Check if Redis requires password, TLS, or ACL users.
5. **Existing tooling**: Look for `redis-cli`, `redis-py`, or `StackExchange.Redis` usage in the project.

Use these signals to choose the right task, shell, and safety level.

## Quick Start

1. Choose one task:
   - `health-check`
   - `memory-audit`
   - `slowlog-report`
   - `client-report`
   - `keyspace-scan`
   - `cleanup-by-pattern`
2. Choose one script target:
   - `powershell`
   - `bash`
   - `python`
3. Generate the bundle:

```powershell
python scripts/generate_redis_maintenance_bundle.py --task health-check --shell powershell --output-dir ./out/redis-health
```

4. Read `redis-maintenance-bundle.json` before touching the generated script.
5. Fill `REDIS_URL` and any task placeholders.
6. Run the generated script in dry-run or read-only mode first.

## Workflow

### 1. Choose The Smallest Useful Task

- Use `health-check` when the incident is still vague and you need a baseline snapshot.
- Use `memory-audit` when memory pressure, evictions, or oversized keys are suspected.
- Use `slowlog-report` when latency spikes or slow commands are the active symptom.
- Use `client-report` when connection spikes, blocked clients, or replica status need a fast report.
- Use `keyspace-scan` when you need type and TTL evidence for one key family.
- Use `cleanup-by-pattern` only after you already know the target key family and have reviewed a preview.

Read `references/task-catalog.md` when you need the full task matrix, risk levels, or shell guidance.

### 2. Generate Instead Of Freehand Guessing

Run the helper script with one task and one shell. Treat the output bundle as the source of truth for:

- generated script name,
- required environment variables,
- safety notes,
- verification commands,
- and follow-up references.

Do not hand-write ad-hoc Redis maintenance snippets when the helper already covers the task.

### 3. Review The Bundle Before Running Anything

Check these sections first:

- `risk_level`
- `env_vars`
- `placeholders`
- `safety_notes`
- `verification_commands`

If the generated task is `cleanup-by-pattern`, do not skip the preview. The generated cleanup scripts default to dry-run on purpose.

### 4. Run The Lowest-Risk Path First

- For read-only tasks, start with the narrowest pattern or limit that still proves the issue.
- For `cleanup-by-pattern`, preview the matching keys, inspect TTL and memory usage, then enable execution only after the key list looks correct.
- Report exactly what was generated, what was run, and what remains unverified.

## Guardrails

- Do not use `KEYS` for large or shared databases when `SCAN` already fits the task.
- Do not add `FLUSHDB`, `FLUSHALL`, or `CONFIG SET` to the generated scripts.
- Do not hardcode credentials; keep connection data in `REDIS_URL` or equivalent environment variables.
- Do not treat `cleanup-by-pattern` as safe by default. Preview first, bound the pattern, and keep an explicit limit.
- Do not claim a production-safe fix when you only generated the bundle and did not run the verification commands.
- Do not replace existing backup, observability, or failover workflows unless the user explicitly asks for that broader change.

## Examples

### Example 1: Generate a health check bundle

```powershell
python scripts/generate_redis_maintenance_bundle.py --task health-check --shell powershell --output-dir ./out/redis-health
```

### Example 2: Generate a memory audit in Bash

```bash
python scripts/generate_redis_maintenance_bundle.py --task memory-audit --shell bash --output-dir ./out/redis-memory
```

## References

- Read `references/task-catalog.md` for task selection, shell choice, and output expectations.
- Read `references/safety-rules.md` before using the cleanup or scan-oriented tasks on a live system.
- Read `references/command-notes.md` for current Redis command notes and redis-py connection guidance.

## Helper Script

Run:

```powershell
python scripts/generate_redis_maintenance_bundle.py --task <health-check|memory-audit|slowlog-report|client-report|keyspace-scan|cleanup-by-pattern> --shell <powershell|bash|python> --output-dir <output-dir>
```

Use `redis-maintenance-bundle.json` as the machine-readable truth and `redis-maintenance-bundle.md` as the human review surface.
