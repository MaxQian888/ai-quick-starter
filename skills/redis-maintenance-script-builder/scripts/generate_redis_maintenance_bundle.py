#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass(frozen=True)
class TaskDefinition:
    summary: str
    risk_level: str
    env_vars: tuple[str, ...]
    placeholders: tuple[str, ...]
    safety_notes: tuple[str, ...]
    verification_commands: tuple[str, ...]


TASKS: dict[str, TaskDefinition] = {
    "health-check": TaskDefinition(
        summary="Collect a fast, read-only Redis health snapshot with connectivity, client, stats, and memory views.",
        risk_level="low",
        env_vars=("REDIS_URL", "REDIS_CLI"),
        placeholders=("REDIS_URL",),
        safety_notes=(
            "Prefer this task first when the failure mode is still unclear.",
            "Keep the command surface read-only; do not add CONFIG SET or FLUSH commands.",
            "Capture INFO output before changing any runtime setting.",
        ),
        verification_commands=(
            "redis-cli -u \"$REDIS_URL\" PING",
            "redis-cli -u \"$REDIS_URL\" INFO memory",
            "redis-cli -u \"$REDIS_URL\" INFO stats",
        ),
    ),
    "memory-audit": TaskDefinition(
        summary="Inspect Redis memory pressure, top key patterns, and sampled key size signals without blocking the server.",
        risk_level="medium",
        env_vars=("REDIS_URL", "REDIS_CLI"),
        placeholders=("REDIS_URL", "PATTERN", "SAMPLE_LIMIT"),
        safety_notes=(
            "Prefer SCAN-driven sampling over KEYS on shared or large databases.",
            "Compare sampled keys with redis-cli --bigkeys or --memkeys before deciding on cleanup.",
            "Correlate memory findings with slow commands before changing eviction or key layout.",
        ),
        verification_commands=(
            "redis-cli -u \"$REDIS_URL\" INFO memory",
            "redis-cli -u \"$REDIS_URL\" MEMORY STATS",
            "redis-cli -u \"$REDIS_URL\" --bigkeys",
            "redis-cli -u \"$REDIS_URL\" --memkeys",
        ),
    ),
    "slowlog-report": TaskDefinition(
        summary="Capture Redis latency and slow command evidence for later triage without mutating state.",
        risk_level="low",
        env_vars=("REDIS_URL", "REDIS_CLI"),
        placeholders=("REDIS_URL", "ENTRY_LIMIT"),
        safety_notes=(
            "Review SLOWLOG and LATENCY output before guessing which commands are causing spikes.",
            "Replace KEYS, HGETALL, or wide scans in application code before blaming Redis itself.",
            "Keep the collection window narrow enough that the log still maps to the current incident.",
        ),
        verification_commands=(
            "redis-cli -u \"$REDIS_URL\" SLOWLOG LEN",
            "redis-cli -u \"$REDIS_URL\" SLOWLOG GET 32",
            "redis-cli -u \"$REDIS_URL\" LATENCY LATEST",
        ),
    ),
    "client-report": TaskDefinition(
        summary="Collect client, replication, and connection evidence for Redis connection-pressure or failover triage.",
        risk_level="low",
        env_vars=("REDIS_URL", "REDIS_CLI"),
        placeholders=("REDIS_URL",),
        safety_notes=(
            "Use this when connection spikes, blocked clients, or replica drift are the main symptoms.",
            "Capture INFO clients and replication before changing client-output-buffer, timeout, or failover settings.",
            "Treat CLIENT LIST as point-in-time evidence and correlate it with application connection pooling behavior.",
        ),
        verification_commands=(
            "redis-cli -u \"$REDIS_URL\" INFO clients",
            "redis-cli -u \"$REDIS_URL\" INFO replication",
            "redis-cli -u \"$REDIS_URL\" CLIENT INFO",
            "redis-cli -u \"$REDIS_URL\" CLIENT LIST",
        ),
    ),
    "keyspace-scan": TaskDefinition(
        summary="Sample matching keys, types, and TTLs with SCAN so you can review key ownership safely.",
        risk_level="medium",
        env_vars=("REDIS_URL", "REDIS_CLI"),
        placeholders=("REDIS_URL", "PATTERN", "LIMIT"),
        safety_notes=(
            "Use SCAN with pattern filters and optional pacing instead of KEYS.",
            "Sample TTL and TYPE before assuming a key family is safe to delete or rewrite.",
            "Keep limits explicit so the first run stays reviewable.",
        ),
        verification_commands=(
            "redis-cli -u \"$REDIS_URL\" --scan --pattern 'session:*'",
            "redis-cli -u \"$REDIS_URL\" TTL session:demo",
            "redis-cli -u \"$REDIS_URL\" TYPE session:demo",
        ),
    ),
    "cleanup-by-pattern": TaskDefinition(
        summary="Generate a guarded cleanup script that defaults to dry-run and only executes UNLINK after preview.",
        risk_level="high",
        env_vars=("REDIS_URL", "REDIS_CLI"),
        placeholders=("REDIS_URL", "PATTERN", "LIMIT"),
        safety_notes=(
            "Keep dry-run on for the first pass and review the key list before enabling execution.",
            "Use UNLINK for asynchronous deletion when possible; avoid FLUSH* and wildcard delete shortcuts.",
            "Bound the cleanup by pattern and limit so rollback analysis remains possible.",
        ),
        verification_commands=(
            "redis-cli -u \"$REDIS_URL\" --scan --pattern 'session:*'",
            "redis-cli -u \"$REDIS_URL\" TTL session:demo",
            "redis-cli -u \"$REDIS_URL\" MEMORY USAGE session:demo",
        ),
    ),
}

SHELL_EXTENSIONS = {
    "powershell": "ps1",
    "bash": "sh",
    "python": "py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Redis maintenance script bundles for common audit and cleanup tasks."
    )
    parser.add_argument("--task", required=True, choices=sorted(TASKS))
    parser.add_argument("--shell", required=True, choices=sorted(SHELL_EXTENSIONS))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    return parser.parse_args()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def shell_script_name(task: str, shell: str) -> str:
    return f"redis-{task}.{SHELL_EXTENSIONS[shell]}"


def render_powershell(task: str) -> str:
    if task == "health-check":
        return dedent(
            """\
            [CmdletBinding()]
            param(
              [string]$RedisUrl = $env:REDIS_URL,
              [string]$RedisCli = $env:REDIS_CLI
            )

            if (-not $RedisCli) { $RedisCli = "redis-cli" }
            if (-not $RedisUrl) { throw "Set REDIS_URL or pass -RedisUrl." }

            function Invoke-RedisCli {
              param([string[]]$Args)
              & $RedisCli -u $RedisUrl @Args
            }

            Write-Host "== PING =="
            Invoke-RedisCli @("PING")

            Write-Host "== INFO server =="
            Invoke-RedisCli @("INFO", "server")

            Write-Host "== INFO clients =="
            Invoke-RedisCli @("INFO", "clients")

            Write-Host "== INFO stats =="
            Invoke-RedisCli @("INFO", "stats")

            Write-Host "== INFO memory =="
            Invoke-RedisCli @("INFO", "memory")

            Write-Host "== INFO persistence =="
            Invoke-RedisCli @("INFO", "persistence")
            """
        )
    if task == "memory-audit":
        return dedent(
            """\
            [CmdletBinding()]
            param(
              [string]$RedisUrl = $env:REDIS_URL,
              [string]$RedisCli = $env:REDIS_CLI,
              [string]$Pattern = "*",
              [int]$Limit = 200,
              [double]$ScanIntervalSeconds = 0.01
            )

            if (-not $RedisCli) { $RedisCli = "redis-cli" }
            if (-not $RedisUrl) { throw "Set REDIS_URL or pass -RedisUrl." }

            function Invoke-RedisCli {
              param([string[]]$Args)
              & $RedisCli -u $RedisUrl @Args
            }

            Write-Host "== INFO memory =="
            Invoke-RedisCli @("INFO", "memory")

            Write-Host "== MEMORY STATS =="
            Invoke-RedisCli @("MEMORY", "STATS")

            Write-Host "== MEMORY DOCTOR =="
            try {
              Invoke-RedisCli @("MEMORY", "DOCTOR")
            } catch {
              Write-Warning "MEMORY DOCTOR is unavailable on this server."
            }

            Write-Host "== redis-cli --bigkeys =="
            & $RedisCli -u $RedisUrl --bigkeys

            Write-Host "== redis-cli --memkeys =="
            & $RedisCli -u $RedisUrl --memkeys

            Write-Host "== Sampled keys =="
            $keys = & $RedisCli -u $RedisUrl --scan --pattern $Pattern -i $ScanIntervalSeconds | Select-Object -First $Limit
            foreach ($key in $keys) {
              $type = Invoke-RedisCli @("TYPE", $key)
              $ttl = Invoke-RedisCli @("TTL", $key)
              $usage = Invoke-RedisCli @("MEMORY", "USAGE", $key)
              "{0}`tTYPE={1}`tTTL={2}`tMEMORY={3}" -f $key, $type, $ttl, $usage
            }
            """
        )
    if task == "slowlog-report":
        return dedent(
            """\
            [CmdletBinding()]
            param(
              [string]$RedisUrl = $env:REDIS_URL,
              [string]$RedisCli = $env:REDIS_CLI,
              [int]$EntryLimit = 32
            )

            if (-not $RedisCli) { $RedisCli = "redis-cli" }
            if (-not $RedisUrl) { throw "Set REDIS_URL or pass -RedisUrl." }

            function Invoke-RedisCli {
              param([string[]]$Args)
              & $RedisCli -u $RedisUrl @Args
            }

            Write-Host "== SLOWLOG LEN =="
            Invoke-RedisCli @("SLOWLOG", "LEN")

            Write-Host "== SLOWLOG GET =="
            Invoke-RedisCli @("SLOWLOG", "GET", "$EntryLimit")

            Write-Host "== LATENCY LATEST =="
            try {
              Invoke-RedisCli @("LATENCY", "LATEST")
            } catch {
              Write-Warning "LATENCY LATEST is unavailable on this server."
            }
            """
        )
    if task == "client-report":
        return dedent(
            """\
            [CmdletBinding()]
            param(
              [string]$RedisUrl = $env:REDIS_URL,
              [string]$RedisCli = $env:REDIS_CLI
            )

            if (-not $RedisCli) { $RedisCli = "redis-cli" }
            if (-not $RedisUrl) { throw "Set REDIS_URL or pass -RedisUrl." }

            function Invoke-RedisCli {
              param([string[]]$Args)
              & $RedisCli -u $RedisUrl @Args
            }

            Write-Host "== INFO clients =="
            Invoke-RedisCli @("INFO", "clients")

            Write-Host "== INFO replication =="
            Invoke-RedisCli @("INFO", "replication")

            Write-Host "== CLIENT INFO =="
            try {
              Invoke-RedisCli @("CLIENT", "INFO")
            } catch {
              Write-Warning "CLIENT INFO is unavailable on this server."
            }

            Write-Host "== CLIENT LIST =="
            Invoke-RedisCli @("CLIENT", "LIST")
            """
        )
    if task == "keyspace-scan":
        return dedent(
            """\
            [CmdletBinding()]
            param(
              [string]$RedisUrl = $env:REDIS_URL,
              [string]$RedisCli = $env:REDIS_CLI,
              [string]$Pattern = "*",
              [int]$Limit = 200,
              [double]$ScanIntervalSeconds = 0.01
            )

            if (-not $RedisCli) { $RedisCli = "redis-cli" }
            if (-not $RedisUrl) { throw "Set REDIS_URL or pass -RedisUrl." }

            function Invoke-RedisCli {
              param([string[]]$Args)
              & $RedisCli -u $RedisUrl @Args
            }

            $keys = & $RedisCli -u $RedisUrl --scan --pattern $Pattern -i $ScanIntervalSeconds | Select-Object -First $Limit
            foreach ($key in $keys) {
              $type = Invoke-RedisCli @("TYPE", $key)
              $ttl = Invoke-RedisCli @("TTL", $key)
              "{0}`tTYPE={1}`tTTL={2}" -f $key, $type, $ttl
            }
            """
        )
    if task == "cleanup-by-pattern":
        return dedent(
            """\
            [CmdletBinding()]
            param(
              [string]$RedisUrl = $env:REDIS_URL,
              [string]$RedisCli = $env:REDIS_CLI,
              [string]$Pattern = "session:*",
              [int]$Limit = 200,
              [double]$ScanIntervalSeconds = 0.01,
              [switch]$Execute
            )

            if (-not $RedisCli) { $RedisCli = "redis-cli" }
            if (-not $RedisUrl) { throw "Set REDIS_URL or pass -RedisUrl." }

            function Invoke-RedisCli {
              param([string[]]$Args)
              & $RedisCli -u $RedisUrl @Args
            }

            $keys = & $RedisCli -u $RedisUrl --scan --pattern $Pattern -i $ScanIntervalSeconds | Select-Object -First $Limit
            if (-not $keys) {
              Write-Host "No matching keys found."
              return
            }

            Write-Host "Dry run preview. Matching keys:"
            foreach ($key in $keys) {
              $ttl = Invoke-RedisCli @("TTL", $key)
              $usage = Invoke-RedisCli @("MEMORY", "USAGE", $key)
              "{0}`tTTL={1}`tMEMORY={2}" -f $key, $ttl, $usage
            }

            if (-not $Execute) {
              Write-Warning "Dry run only. Re-run with -Execute to call UNLINK on the previewed keys."
              return
            }

            foreach ($key in $keys) {
              Invoke-RedisCli @("UNLINK", $key)
            }
            """
        )
    raise ValueError(f"Unsupported task: {task}")


def render_bash(task: str) -> str:
    if task == "health-check":
        return dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            REDIS_URL="${REDIS_URL:-${1:-}}"
            REDIS_CLI="${REDIS_CLI:-redis-cli}"

            if [[ -z "${REDIS_URL}" ]]; then
              echo "Set REDIS_URL or pass the URL as the first argument." >&2
              exit 1
            fi

            run() {
              "${REDIS_CLI}" -u "${REDIS_URL}" "$@"
            }

            echo "== PING =="
            run PING

            for section in server clients stats memory persistence; do
              echo "== INFO ${section} =="
              run INFO "${section}"
            done
            """
        )
    if task == "memory-audit":
        return dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            REDIS_URL="${REDIS_URL:-${1:-}}"
            REDIS_CLI="${REDIS_CLI:-redis-cli}"
            PATTERN="${PATTERN:-*}"
            LIMIT="${LIMIT:-200}"
            SCAN_INTERVAL_SECONDS="${SCAN_INTERVAL_SECONDS:-0.01}"

            if [[ -z "${REDIS_URL}" ]]; then
              echo "Set REDIS_URL or pass the URL as the first argument." >&2
              exit 1
            fi

            run() {
              "${REDIS_CLI}" -u "${REDIS_URL}" "$@"
            }

            echo "== INFO memory =="
            run INFO memory

            echo "== MEMORY STATS =="
            run MEMORY STATS

            echo "== MEMORY DOCTOR =="
            run MEMORY DOCTOR || true

            echo "== redis-cli --bigkeys =="
            "${REDIS_CLI}" -u "${REDIS_URL}" --bigkeys

            echo "== redis-cli --memkeys =="
            "${REDIS_CLI}" -u "${REDIS_URL}" --memkeys

            echo "== Sampled keys =="
            count=0
            while IFS= read -r key; do
              ((count+=1))
              if (( count > LIMIT )); then
                break
              fi
              type="$(run TYPE "${key}")"
              ttl="$(run TTL "${key}")"
              usage="$(run MEMORY USAGE "${key}")"
              printf '%s\\tTYPE=%s\\tTTL=%s\\tMEMORY=%s\\n' "${key}" "${type}" "${ttl}" "${usage}"
            done < <("${REDIS_CLI}" -u "${REDIS_URL}" --scan --pattern "${PATTERN}" -i "${SCAN_INTERVAL_SECONDS}")
            """
        )
    if task == "slowlog-report":
        return dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            REDIS_URL="${REDIS_URL:-${1:-}}"
            REDIS_CLI="${REDIS_CLI:-redis-cli}"
            ENTRY_LIMIT="${ENTRY_LIMIT:-32}"

            if [[ -z "${REDIS_URL}" ]]; then
              echo "Set REDIS_URL or pass the URL as the first argument." >&2
              exit 1
            fi

            run() {
              "${REDIS_CLI}" -u "${REDIS_URL}" "$@"
            }

            echo "== SLOWLOG LEN =="
            run SLOWLOG LEN

            echo "== SLOWLOG GET =="
            run SLOWLOG GET "${ENTRY_LIMIT}"

            echo "== LATENCY LATEST =="
            run LATENCY LATEST || true
            """
        )
    if task == "client-report":
        return dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            REDIS_URL="${REDIS_URL:-${1:-}}"
            REDIS_CLI="${REDIS_CLI:-redis-cli}"

            if [[ -z "${REDIS_URL}" ]]; then
              echo "Set REDIS_URL or pass the URL as the first argument." >&2
              exit 1
            fi

            run() {
              "${REDIS_CLI}" -u "${REDIS_URL}" "$@"
            }

            echo "== INFO clients =="
            run INFO clients

            echo "== INFO replication =="
            run INFO replication

            echo "== CLIENT INFO =="
            run CLIENT INFO || true

            echo "== CLIENT LIST =="
            run CLIENT LIST
            """
        )
    if task == "keyspace-scan":
        return dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            REDIS_URL="${REDIS_URL:-${1:-}}"
            REDIS_CLI="${REDIS_CLI:-redis-cli}"
            PATTERN="${PATTERN:-*}"
            LIMIT="${LIMIT:-200}"
            SCAN_INTERVAL_SECONDS="${SCAN_INTERVAL_SECONDS:-0.01}"

            if [[ -z "${REDIS_URL}" ]]; then
              echo "Set REDIS_URL or pass the URL as the first argument." >&2
              exit 1
            fi

            run() {
              "${REDIS_CLI}" -u "${REDIS_URL}" "$@"
            }

            count=0
            while IFS= read -r key; do
              ((count+=1))
              if (( count > LIMIT )); then
                break
              fi
              type="$(run TYPE "${key}")"
              ttl="$(run TTL "${key}")"
              printf '%s\\tTYPE=%s\\tTTL=%s\\n' "${key}" "${type}" "${ttl}"
            done < <("${REDIS_CLI}" -u "${REDIS_URL}" --scan --pattern "${PATTERN}" -i "${SCAN_INTERVAL_SECONDS}")
            """
        )
    if task == "cleanup-by-pattern":
        return dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            REDIS_URL="${REDIS_URL:-${1:-}}"
            REDIS_CLI="${REDIS_CLI:-redis-cli}"
            PATTERN="${PATTERN:-session:*}"
            LIMIT="${LIMIT:-200}"
            SCAN_INTERVAL_SECONDS="${SCAN_INTERVAL_SECONDS:-0.01}"
            EXECUTE="${EXECUTE:-0}"

            if [[ -z "${REDIS_URL}" ]]; then
              echo "Set REDIS_URL or pass the URL as the first argument." >&2
              exit 1
            fi

            run() {
              "${REDIS_CLI}" -u "${REDIS_URL}" "$@"
            }

            mapfile -t keys < <("${REDIS_CLI}" -u "${REDIS_URL}" --scan --pattern "${PATTERN}" -i "${SCAN_INTERVAL_SECONDS}" | head -n "${LIMIT}")

            if (( ${#keys[@]} == 0 )); then
              echo "No matching keys found."
              exit 0
            fi

            echo "Dry run preview. Matching keys:"
            for key in "${keys[@]}"; do
              ttl="$(run TTL "${key}")"
              usage="$(run MEMORY USAGE "${key}")"
              printf '%s\\tTTL=%s\\tMEMORY=%s\\n' "${key}" "${ttl}" "${usage}"
            done

            if [[ "${EXECUTE}" != "1" ]]; then
              echo "Dry run only. Re-run with EXECUTE=1 to call UNLINK on the previewed keys." >&2
              exit 0
            fi

            for key in "${keys[@]}"; do
              run UNLINK "${key}"
            done
            """
        )
    raise ValueError(f"Unsupported task: {task}")


def render_python(task: str) -> str:
    common_imports = dedent(
        """\
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        import os
        import sys

        import redis
        """
    )
    common_parser = dedent(
        """\
        def add_common_arguments(parser: argparse.ArgumentParser) -> None:
            parser.add_argument("--redis-url", default=os.environ.get("REDIS_URL", ""))
            parser.add_argument("--pattern", default=os.environ.get("PATTERN", "*"))
            parser.add_argument("--limit", type=int, default=int(os.environ.get("LIMIT", "200")))


        def build_client(redis_url: str) -> redis.Redis:
            if not redis_url:
                raise SystemExit("Set REDIS_URL or pass --redis-url.")
            return redis.from_url(
                redis_url,
                decode_responses=True,
                health_check_interval=2,
            )
        """
    )
    if task == "health-check":
        return common_imports + "\n" + common_parser + "\n" + dedent(
            """\
            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser(description="Redis health check")
                add_common_arguments(parser)
                return parser.parse_args()


            def main() -> int:
                args = parse_args()
                client = build_client(args.redis_url)
                payload = {
                    "ping": client.ping(),
                    "server": client.info(section="server"),
                    "clients": client.info(section="clients"),
                    "stats": client.info(section="stats"),
                    "memory": client.info(section="memory"),
                    "persistence": client.info(section="persistence"),
                }
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        )
    if task == "memory-audit":
        return common_imports + "\n" + common_parser + "\n" + dedent(
            """\
            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser(description="Redis memory audit")
                add_common_arguments(parser)
                parser.add_argument(
                    "--sample-limit",
                    type=int,
                    default=int(os.environ.get("SAMPLE_LIMIT", "50")),
                )
                return parser.parse_args()


            def main() -> int:
                args = parse_args()
                client = build_client(args.redis_url)
                memory_info = client.info(section="memory")
                try:
                    memory_stats = client.memory_stats()
                except redis.ResponseError as exc:
                    memory_stats = {"error": str(exc)}

                sampled_keys: list[dict[str, object]] = []
                for index, key in enumerate(client.scan_iter(match=args.pattern, count=args.limit), start=1):
                    if index > args.sample_limit:
                        break
                    try:
                        memory_usage = client.memory_usage(key)
                    except redis.ResponseError:
                        memory_usage = None
                    sampled_keys.append(
                        {
                            "key": key,
                            "type": client.type(key),
                            "ttl": client.ttl(key),
                            "memory_usage": memory_usage,
                        }
                    )

                payload = {
                    "memory": memory_info,
                    "memory_stats": memory_stats,
                    "sampled_keys": sampled_keys,
                    "sample_limit": args.sample_limit,
                }
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        )
    if task == "slowlog-report":
        return common_imports + "\n" + common_parser + "\n" + dedent(
            """\
            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser(description="Redis slowlog report")
                add_common_arguments(parser)
                parser.add_argument(
                    "--entry-limit",
                    type=int,
                    default=int(os.environ.get("ENTRY_LIMIT", "32")),
                )
                return parser.parse_args()


            def main() -> int:
                args = parse_args()
                client = build_client(args.redis_url)
                payload = {
                    "slowlog_length": client.execute_command("SLOWLOG", "LEN"),
                    "slowlog_entries": client.slowlog_get(args.entry_limit),
                }
                try:
                    payload["latency_latest"] = client.execute_command("LATENCY", "LATEST")
                except redis.ResponseError as exc:
                    payload["latency_latest"] = {"error": str(exc)}
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        )
    if task == "client-report":
        return common_imports + "\n" + common_parser + "\n" + dedent(
            """\
            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser(description="Redis client report")
                add_common_arguments(parser)
                return parser.parse_args()


            def main() -> int:
                args = parse_args()
                client = build_client(args.redis_url)
                # CLIENT LIST gives the point-in-time connection snapshot.
                payload = {
                    "clients": client.info(section="clients"),
                    "replication": client.info(section="replication"),
                    "client_list": client.execute_command("CLIENT", "LIST"),
                }
                try:
                    # CLIENT INFO can fail on older Redis servers, so keep it soft.
                    payload["client_info"] = client.execute_command("CLIENT", "INFO")
                except redis.ResponseError as exc:
                    payload["client_info"] = {"error": str(exc)}
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        )
    if task == "keyspace-scan":
        return common_imports + "\n" + common_parser + "\n" + dedent(
            """\
            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser(description="Redis keyspace scan")
                add_common_arguments(parser)
                return parser.parse_args()


            def main() -> int:
                args = parse_args()
                client = build_client(args.redis_url)
                rows = []
                for index, key in enumerate(client.scan_iter(match=args.pattern, count=args.limit), start=1):
                    if index > args.limit:
                        break
                    rows.append(
                        {
                            "key": key,
                            "type": client.type(key),
                            "ttl": client.ttl(key),
                        }
                    )
                print(json.dumps({"keys": rows, "pattern": args.pattern}, ensure_ascii=False, indent=2))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        )
    if task == "cleanup-by-pattern":
        return common_imports + "\n" + common_parser + "\n" + dedent(
            """\
            def parse_args() -> argparse.Namespace:
                parser = argparse.ArgumentParser(description="Redis cleanup by pattern")
                add_common_arguments(parser)
                parser.add_argument("--execute", action="store_true")
                return parser.parse_args()


            def main() -> int:
                args = parse_args()
                client = build_client(args.redis_url)
                keys = []
                for index, key in enumerate(client.scan_iter(match=args.pattern, count=args.limit), start=1):
                    if index > args.limit:
                        break
                    keys.append(
                        {
                            "key": key,
                            "ttl": client.ttl(key),
                            "memory_usage": client.memory_usage(key),
                        }
                    )

                if not args.execute:
                    print(json.dumps({"dry_run": True, "keys": keys}, ensure_ascii=False, indent=2))
                    print("Dry run only. Re-run with --execute to call UNLINK on the previewed keys.", file=sys.stderr)
                    return 0

                with client.pipeline(transaction=False) as pipe:
                    for row in keys:
                        pipe.unlink(row["key"])
                    pipe.execute()

                print(json.dumps({"dry_run": False, "deleted_keys": [row["key"] for row in keys]}, ensure_ascii=False, indent=2))
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        )
    raise ValueError(f"Unsupported task: {task}")


def render_script(task: str, shell: str) -> str:
    if shell == "powershell":
        return render_powershell(task)
    if shell == "bash":
        return render_bash(task)
    if shell == "python":
        return render_python(task)
    raise ValueError(f"Unsupported shell: {shell}")


def build_payload(task: str, shell: str, output_dir: Path, script_name: str) -> dict[str, object]:
    definition = TASKS[task]
    script_path = output_dir / script_name
    json_name = "redis-maintenance-bundle.json"
    markdown_name = "redis-maintenance-bundle.md"
    env_vars = ["REDIS_URL"] if shell == "python" else list(definition.env_vars)
    return {
        "task": task,
        "shell": shell,
        "summary": definition.summary,
        "risk_level": definition.risk_level,
        "script_name": script_name,
        "script_path": str(script_path),
        "env_vars": env_vars,
        "placeholders": list(definition.placeholders),
        "safety_notes": list(definition.safety_notes),
        "verification_commands": list(definition.verification_commands),
        "references": [
            "references/task-catalog.md",
            "references/safety-rules.md",
            "references/command-notes.md",
        ],
        "generated_files": [
            script_name,
            json_name,
            markdown_name,
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Redis Maintenance Bundle",
        "",
        "## Summary",
        "",
        f"- Task: `{payload['task']}`",
        f"- Shell: `{payload['shell']}`",
        f"- Risk level: `{payload['risk_level']}`",
        f"- Script: `{payload['script_name']}`",
        "",
        "## Generated Script",
        "",
        f"- `{payload['script_name']}`",
        "",
        "## Environment Variables",
        "",
        *[f"- `{item}`" for item in payload["env_vars"]],
        "",
        "## Safety Notes",
        "",
        *[f"- {item}" for item in payload["safety_notes"]],
        "",
        "## Verification Commands",
        "",
        *[f"- `{item}`" for item in payload["verification_commands"]],
        "",
        "## References",
        "",
        *[f"- `{item}`" for item in payload["references"]],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    script_name = shell_script_name(args.task, args.shell)
    script_path = output_dir / script_name
    script_text = render_script(args.task, args.shell)
    write_text(script_path, script_text)

    if args.shell != "powershell":
        script_path.chmod(script_path.stat().st_mode | 0o111)

    payload = build_payload(args.task, args.shell, output_dir, script_name)

    json_path = Path(args.json_out).resolve() if args.json_out else output_dir / "redis-maintenance-bundle.json"
    markdown_path = (
        Path(args.markdown_out).resolve()
        if args.markdown_out
        else output_dir / "redis-maintenance-bundle.md"
    )

    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_text(markdown_path, render_markdown(payload))

    print(
        json.dumps(
            {
                "task": args.task,
                "shell": args.shell,
                "script": str(script_path),
                "json": str(json_path),
                "markdown": str(markdown_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
