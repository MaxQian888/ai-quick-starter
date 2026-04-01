#!/usr/bin/env python3
"""Normalize multi-track software research findings into one brief."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def dedupe(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    output: list[Any] = []
    for item in items:
        marker = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
        if marker not in seen:
            seen.add(marker)
            output.append(item)
    return output


def merge_findings(findings: Any) -> dict[str, Any]:
    if isinstance(findings, dict):
        findings = findings.get("findings", [])
    if not isinstance(findings, list):
        raise TypeError("findings must be a list of track entries")
    if not findings:
        raise ValueError("findings cannot be empty")

    software = findings[0].get("software", "Unknown Software")
    versions: list[str] = []
    platforms: list[str] = []
    prerequisites: list[str] = []
    core_concepts: list[str] = []
    command_inventory: list[str] = []
    source_inventory: list[dict[str, str]] = []
    verified_claims: list[str] = []
    unresolved_questions: list[str] = []
    topic_notes: dict[str, list[str]] = defaultdict(list)

    for finding in findings:
        if finding.get("software") and finding["software"] != software:
            raise ValueError("all findings must target the same software")
        if finding.get("version"):
            versions.append(finding["version"])
        platforms.extend(finding.get("platforms", []))
        prerequisites.extend(finding.get("prerequisites", []))
        core_concepts.extend(finding.get("core_concepts", []))
        command_inventory.extend(finding.get("commands", []))
        if finding.get("source"):
            source_inventory.append(
                {
                    "track": finding.get("track", "unknown"),
                    "source": finding.get("source", "unknown"),
                    "url": finding.get("url", ""),
                }
            )
        if finding.get("verified") and finding.get("claim"):
            verified_claims.append(finding["claim"])
        unresolved_questions.extend(finding.get("questions", []))
        topic = finding.get("topic")
        claim = finding.get("claim")
        if topic and claim:
            topic_notes[topic].append(claim)

    return {
        "software": software,
        "versions": dedupe(versions),
        "platforms": dedupe(platforms),
        "prerequisites": dedupe(prerequisites),
        "core_concepts": dedupe(core_concepts),
        "command_inventory": dedupe(command_inventory),
        "source_inventory": dedupe(source_inventory),
        "verified_claims": dedupe(verified_claims),
        "unresolved_questions": dedupe(unresolved_questions),
        "topic_notes": {topic: dedupe(notes) for topic, notes in topic_notes.items()},
    }


def render_markdown(brief: dict[str, Any]) -> str:
    versions = ", ".join(brief.get("versions", [])) or "unspecified"
    platforms = ", ".join(brief.get("platforms", [])) or "unspecified"
    lines = [
        f"# {brief['software']} Research Brief",
        "",
        f"- Versions: {versions}",
        f"- Platforms: {platforms}",
        "",
        "## Prerequisites",
    ]
    prerequisites = brief.get("prerequisites", []) or ["None recorded"]
    lines.extend(f"- {item}" for item in prerequisites)
    lines.extend(["", "## Core Concepts"])
    concepts = brief.get("core_concepts", []) or ["None recorded"]
    lines.extend(f"- {item}" for item in concepts)
    lines.extend(["", "## Command Inventory"])
    commands = brief.get("command_inventory", []) or ["None recorded"]
    lines.extend(f"- {item}" for item in commands)
    lines.extend(["", "## Source Inventory"])
    for source in brief.get("source_inventory", []) or [{"track": "unknown", "source": "None recorded", "url": ""}]:
        if source.get("url"):
            lines.append(f"- [{source['track']}] {source['source']}: {source['url']}")
        else:
            lines.append(f"- [{source['track']}] {source['source']}")
    lines.extend(["", "## Verified Claims"])
    verified = brief.get("verified_claims", []) or ["None recorded"]
    lines.extend(f"- {item}" for item in verified)
    lines.extend(["", "## Unresolved Questions"])
    questions = brief.get("unresolved_questions", []) or ["None recorded"]
    lines.extend(f"- {item}" for item in questions)
    topic_notes = brief.get("topic_notes", {})
    if topic_notes:
        lines.extend(["", "## Topic Notes"])
        for topic, notes in topic_notes.items():
            lines.append(f"### {topic.capitalize()}")
            lines.extend(f"- {item}" for item in notes)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normalized software research brief.")
    parser.add_argument("--input", required=True, help="Path to a JSON file containing raw findings")
    parser.add_argument("--output", help="Optional output path")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = json.loads(Path(args.input).read_text(encoding="utf-8"))
    brief = merge_findings(findings)
    rendered = json.dumps(brief, indent=2) if args.format == "json" else render_markdown(brief)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
