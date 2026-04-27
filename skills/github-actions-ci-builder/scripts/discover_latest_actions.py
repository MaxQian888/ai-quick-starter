#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from github_actions_support import GitHubApiError, build_component_payload, workflow_status_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover GitHub Actions components and resolve the latest stable refs."
    )
    parser.add_argument("--query", help="Free-form need or stack query, for example: 'node pnpm cache'.")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Specific action repository in owner/repo format. Repeatable.",
    )
    parser.add_argument("--workflow", help="Workflow YAML file to scan for uses: references.")
    parser.add_argument("--limit", type=int, default=4, help="Maximum number of catalog matches to return.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.query and not args.repo and not args.workflow:
        raise SystemExit("Provide at least one of --query, --repo, or --workflow.")

    payload: dict[str, object] = {}
    try:
        if args.query or args.repo:
            payload.update(build_component_payload(repos=args.repo, query=args.query, limit=args.limit))
        if args.workflow:
            payload["workflow_scan"] = workflow_status_payload(Path(args.workflow))
    except GitHubApiError as exc:
        message = str(exc)
        if args.as_json:
            print(json.dumps({"error": message}, indent=2))
        else:
            print(message, file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps(payload, indent=2))
        return 0

    for component in payload.get("components", []):
        print(
            f"{component['repo']}: {component['latest_tag']} -> {component['latest_commit_sha']} "
            f"({component['release_url']})"
        )
    workflow_scan = payload.get("workflow_scan")
    if isinstance(workflow_scan, dict):
        print(f"Workflow: {workflow_scan['workflow']}")
        for item in workflow_scan.get("items", []):
            repo = item.get("repo") or item["raw"]
            print(f"  {repo}: {item['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
