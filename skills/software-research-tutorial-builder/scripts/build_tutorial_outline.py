#!/usr/bin/env python3
"""Build a tutorial outline from a normalized research brief."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS = [
    "What This Software Is For",
    "When To Use It And When Not To",
    "Environment And Prerequisites",
    "Installation Or Setup",
    "First Runnable Example",
    "Practical Workflow Example",
    "Common Mistakes And Troubleshooting",
    "Extension Paths And Further Reading",
]


def build_outline(brief: dict[str, Any]) -> str:
    software = brief.get("software", "Unknown Software")
    versions = ", ".join(brief.get("versions", [])) or "Document the current version window"
    platforms = ", ".join(brief.get("platforms", [])) or "Document target platforms"
    prerequisites = brief.get("prerequisites", []) or ["List prerequisites"]
    concepts = brief.get("core_concepts", []) or ["List core concepts"]
    commands = brief.get("command_inventory", []) or ["Add runnable commands"]
    unresolved = brief.get("unresolved_questions", [])

    lines = [f"# {software} Tutorial Outline", "", f"Version scope: {versions}", f"Platforms: {platforms}", ""]
    for index, section in enumerate(REQUIRED_SECTIONS, start=1):
        lines.extend([f"## {index}. {section}", ""])
        if section == "What This Software Is For":
            lines.append(f"- Explain the core problem {software} solves.")
        elif section == "When To Use It And When Not To":
            lines.append("- List strong-fit and weak-fit scenarios.")
        elif section == "Environment And Prerequisites":
            lines.extend([f"- {item}" for item in prerequisites])
        elif section == "Installation Or Setup":
            lines.extend([f"- `{item}`" for item in commands])
        elif section == "First Runnable Example":
            lines.append("- Minimal runnable case")
            lines.append("- Define the success signal for the first run.")
        elif section == "Practical Workflow Example":
            lines.append("- Practical workflow case")
            lines.extend([f"- Highlight concept: {item}" for item in concepts])
        elif section == "Common Mistakes And Troubleshooting":
            lines.append("- Troubleshooting case")
            if brief.get("topic_notes", {}).get("troubleshooting"):
                lines.extend([f"- {item}" for item in brief["topic_notes"]["troubleshooting"]])
            else:
                lines.append("- Add one likely failure mode and recovery path.")
        else:
            lines.append("- Add next-step resources and upgrade paths.")
        lines.append("")

    lines.extend([
        "## Support-Material Checklist",
        "",
        "- [ ] Environment variable example",
        "- [ ] Starter project structure",
        "- [ ] Sample config fragment",
        "- [ ] Sample input or output files",
        "- [ ] Cleanup steps",
        "",
    ])
    conflicts = brief.get("conflicts", {})
    if conflicts:
        lines.extend(["## Conflicts To Resolve", ""])
        for topic, entries in conflicts.items():
            lines.append(f"### {topic.capitalize()}")
            for item in entries:
                lines.append(f"- [{item['track']}] {item['claim']}")
            lines.append("")
    unverified_topics = brief.get("unverified_topics", [])
    if unverified_topics:
        lines.extend(["## Unverified Topics", ""])
        lines.extend([f"- {item}" for item in unverified_topics])
        lines.append("")
    if unresolved:
        lines.extend(["## Open Questions", ""])
        lines.extend([f"- {item}" for item in unresolved])
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON research brief file")
    parser.add_argument("--output", help="Optional output file path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    brief = json.loads(Path(args.input).read_text(encoding="utf-8"))
    outline = build_outline(brief)
    if args.output:
        Path(args.output).write_text(outline, encoding="utf-8")
    else:
        print(outline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
