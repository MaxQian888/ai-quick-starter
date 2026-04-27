#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from github_actions_support import build_ci_orchestration_payload, discover_local_ci_workflows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze GitHub Actions workflow topology, governance, performance, and local verification scope."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--workflow")
    parser.add_argument("--job")
    parser.add_argument("--event")
    parser.add_argument("--plan-local", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"Project root does not exist: {root}", file=sys.stderr)
        return 2

    payload = build_ci_orchestration_payload(
        root=root,
        workflows=discover_local_ci_workflows(root),
        include_local_plan=args.plan_local,
        workflow_filter=args.workflow,
        job_filter=args.job,
        event_name=args.event,
    )

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("Proposed files:")
        for path in payload["proposed_files"]:
            print(f"- {path}")
        print("Repair queue:")
        for item in payload["repair_queue"]:
            print(f"- {item['kind']}: {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
