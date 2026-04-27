#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from github_actions_support import workflow_plan_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a GitHub Actions workflow file and suggest a smaller-file split plan."
    )
    parser.add_argument("--workflow", required=True, help="Path to the workflow YAML file to analyze.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = workflow_plan_payload(Path(args.workflow))

    if args.as_json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Workflow: {payload['workflow_name']}")
    print(f"Triggers: {', '.join(payload['triggers']) or '(none detected)'}")
    print(f"Jobs: {payload['job_count']}")
    for recommendation in payload["recommendations"]:
        print(f"- {recommendation['kind']}: {recommendation['reason']}")
    for target in payload["target_files"]:
        print(f"  -> {target['path']}: {target['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
