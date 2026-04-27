#!/usr/bin/env python3
"""Build or execute a safe installation plan for paper-writing components."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
CURATED_COMPONENTS = {
    "openskills": {
        "repo": "numman-ali/openskills",
        "purpose": "OpenSkills CLI used to install GitHub-hosted skills.",
        "commands": [
            ["node", "--version"],
            ["git", "--version"],
            ["npx", "openskills", "--version"],
            ["npm", "i", "-g", "openskills"],
        ],
        "selectors": [],
    },
    "20-ml-paper-writing": {
        "repo": "zechenzhangAGI/AI-research-SKILLs",
        "purpose": "Conference-oriented paper writing workflow and checklist skill.",
        "commands": [["npx", "openskills", "install", "zechenzhangAGI/AI-research-SKILLs"]],
        "selectors": ["20-ml-paper-writing"],
    },
    "humanizer": {
        "repo": "blader/humanizer",
        "purpose": "Naturalize AI-generated writing before submission.",
        "commands": [["npx", "openskills", "install", "blader/humanizer"]],
        "selectors": [],
    },
    "docx": {
        "repo": "anthropics/skills",
        "purpose": "Read, edit, and redline Word documents.",
        "commands": [["npx", "openskills", "install", "anthropics/skills"]],
        "selectors": ["docx"],
    },
    "doc-coauthoring": {
        "repo": "anthropics/skills",
        "purpose": "Stage-wise document coauthoring workflow.",
        "commands": [["npx", "openskills", "install", "anthropics/skills"]],
        "selectors": ["doc-coauthoring"],
    },
    "canvas-design": {
        "repo": "anthropics/skills",
        "purpose": "Diagram and figure-design workflow for paper visuals.",
        "commands": [["npx", "openskills", "install", "anthropics/skills"]],
        "selectors": ["canvas-design"],
    },
}
CURATED_ORDER = [
    "openskills",
    "20-ml-paper-writing",
    "humanizer",
    "docx",
    "doc-coauthoring",
    "canvas-design",
]


def normalize_component(name: str) -> str:
    normalized = name.strip().lower()
    aliases = {
        "open skills": "openskills",
        "ml-paper-writing": "20-ml-paper-writing",
    }
    return aliases.get(normalized, normalized)


def _command_strings(resolved_components: list[str]) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for component in resolved_components:
        for command in CURATED_COMPONENTS[component]["commands"]:
            rendered = " ".join(command)
            if rendered not in seen:
                commands.append(rendered)
                seen.add(rendered)
    return commands


def build_install_plan(requested: list[str]) -> dict[str, object]:
    if not requested:
        raise ValueError("At least one component is required.")

    normalized = [normalize_component(item) for item in requested]
    if "all" in normalized:
        resolved_components = list(CURATED_ORDER)
    else:
        unknown = [item for item in normalized if item not in CURATED_COMPONENTS]
        if unknown:
            known = ", ".join(CURATED_ORDER)
            raise ValueError(f"Unknown component: {unknown[0]}. Known components: {known}")
        resolved_components = []
        for item in normalized:
            if item not in resolved_components:
                resolved_components.append(item)

    plan = {
        "requested": normalized,
        "resolved_components": resolved_components,
        "commands": _command_strings(resolved_components),
        "components": [],
        "notes": [
            "OpenSkills installs from GitHub and may prompt for skill selection.",
            "anthropics/skills contains multiple skills; select only the requested entries.",
            "Cursor and Claude-style tooling typically discover installed skills under .claude/skills or .cursor/skills.",
        ],
    }
    for component in resolved_components:
        item = CURATED_COMPONENTS[component]
        plan["components"].append(
            {
                "name": component,
                "repo": item["repo"],
                "purpose": item["purpose"],
                "selectors": list(item["selectors"]),
            }
        )
    return plan


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or execute an installation plan for ai-research-writing components.")
    parser.add_argument("components", nargs="+", help="Component names, or 'all' for the full curated set.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable summary.")
    parser.add_argument("--execute", action="store_true", help="Execute the planned commands in order.")
    return parser.parse_args(argv)


def execute_plan(plan: dict[str, object]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for command_text in plan["commands"]:
        command = command_text.split(" ")
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        results.append(
            {
                "command": command_text,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            break
    return results


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan = build_install_plan(args.components)
    if args.execute:
        plan["execution"] = execute_plan(plan)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    print("resolved_components=" + ", ".join(plan["resolved_components"]))
    for command in plan["commands"]:
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
