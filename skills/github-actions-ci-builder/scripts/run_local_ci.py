#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from github_actions_support import (
    analyze_local_ci_plan,
    build_local_ci_payload,
    discover_local_ci_workflows,
    inspect_local_ci_environment,
    run_fallback_commands,
    run_shell_command,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect, plan, and locally execute GitHub Actions workflows with act or fallback commands."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--workflow")
    parser.add_argument("--job")
    parser.add_argument("--mode", choices=("auto", "act", "fallback"), default="auto")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--event")
    parser.add_argument("--matrix", action="append", default=[])
    parser.add_argument("--secret-file")
    parser.add_argument("--env-file")
    parser.add_argument("--input-file")
    parser.add_argument("--event-file")
    parser.add_argument("--container-architecture")
    parser.add_argument("--artifact-server-path")
    parser.add_argument("--platform", action="append", default=[])
    parser.add_argument("--action-offline-mode", action="store_true")
    parser.add_argument("--max-output-chars", type=int, default=12000)
    return parser.parse_args(argv)


def path_or_none(value: str | None) -> Path | None:
    return Path(value) if value else None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"Project root does not exist: {root}", file=sys.stderr)
        return 2

    workflows = discover_local_ci_workflows(root)
    environment = inspect_local_ci_environment()
    plan = analyze_local_ci_plan(
        workflows=workflows,
        environment=environment,
        requested_mode=args.mode,
        workflow_filter=args.workflow,
        job_filter=args.job,
        event_name=args.event,
        matrix_entries=args.matrix,
        secret_file=path_or_none(args.secret_file),
        env_file=path_or_none(args.env_file),
        input_file=path_or_none(args.input_file),
        event_file=path_or_none(args.event_file),
        container_architecture=args.container_architecture,
        artifact_server_path=path_or_none(args.artifact_server_path),
        action_offline_mode=args.action_offline_mode,
        platform_overrides=args.platform,
    )

    if args.discover_only or args.plan_only:
        scoped_plan = dict(plan)
        if args.plan_only:
            scope_limits = list(scoped_plan.get("scope_limits", []))
            scope_limits.append("Local CI path was planned but not executed.")
            scoped_plan["scope_limits"] = scope_limits
        payload = build_local_ci_payload(root, workflows, environment, plan, results=[], overall_status=plan["overall_status"])
        if args.plan_only:
            payload["scope_limits"] = scoped_plan["scope_limits"]
        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Selected mode: {plan['selected_mode']}")
        return 0

    results: list[dict[str, object]] = []
    overall_status = plan["overall_status"]
    if plan["selected_mode"] == "act" and plan["act_command"]:
        result = run_shell_command(root, str(plan["act_command"]), max_output_chars=args.max_output_chars)
        results = [result]
        overall_status = "passed" if result["status"] == "passed" else "failed"
    elif plan["selected_mode"] == "fallback":
        results, overall_status = run_fallback_commands(
            root=root,
            commands=list(plan["runnable_commands"]),
            fail_fast=args.fail_fast,
            max_output_chars=args.max_output_chars,
        )
    else:
        overall_status = "blocked"

    payload = build_local_ci_payload(root, workflows, environment, plan, results=results, overall_status=overall_status)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Selected mode: {plan['selected_mode']}")
        for result in results:
            print(f"{result['status']}: {result['command']}")

    return 0 if overall_status in {"passed", "planned"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
