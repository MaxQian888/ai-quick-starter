# Redis Maintenance Task Catalog

## Task Matrix

| Task | Use when | Risk | Typical shell | Output shape |
| --- | --- | --- | --- | --- |
| `health-check` | Connectivity, client pressure, memory, or persistence need a quick baseline | low | `powershell` or `bash` | one read-only snapshot script |
| `memory-audit` | Memory growth, evictions, or oversized keys are suspected | medium | `python` or `powershell` | memory summary plus sampled key evidence |
| `slowlog-report` | Latency or slow command complaints need server-side evidence | low | `bash` or `powershell` | slowlog and latency capture script |
| `client-report` | Connection spikes, blocked clients, or replica state need investigation | low | `python`, `bash`, or `powershell` | client and replication report |
| `keyspace-scan` | One key family needs TTL and type inspection | medium | any | SCAN-based review script |
| `cleanup-by-pattern` | One reviewed key family must be deleted in a bounded way | high | `powershell` or `python` | dry-run-first cleanup script |

## Shell Selection

- Choose `powershell` when the operator is on Windows and wants a script that is easy to inspect and rerun.
- Choose `bash` when the environment is Linux, container-based, or already standardized on shell automation.
- Choose `python` when the task benefits from structured JSON output, richer sampling logic, or redis-py ergonomics.

## Output Contract

Every generated bundle should contain:

- one script file named `redis-<task>.<ext>`,
- `redis-maintenance-bundle.json`,
- `redis-maintenance-bundle.md`.

The JSON file carries the strongest contract:

- `task`
- `shell`
- `summary`
- `risk_level`
- `script_name`
- `env_vars`
- `placeholders`
- `safety_notes`
- `verification_commands`
- `references`

## Recommended Starting Order

1. `health-check`
2. `slowlog-report` or `memory-audit`
3. `client-report` if the symptom is connections or replica drift
4. `keyspace-scan`
5. `cleanup-by-pattern`

Do not jump directly to cleanup unless the target key family is already proven.
