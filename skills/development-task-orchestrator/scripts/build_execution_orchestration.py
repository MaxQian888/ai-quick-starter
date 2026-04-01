from __future__ import annotations

import argparse
import json
import re
from collections import deque
from pathlib import Path


CHECKLIST_PATTERN = re.compile(r"^-\s*(?:\[[ xX]\]\s*)?(?P<body>.+?)\s*$")
WRITES_PATTERN = re.compile(r"\(writes:\s*(?P<writes>[^)]+)\)\s*$", re.IGNORECASE)
AFTER_PATTERN = re.compile(r"^(?P<title>.+?)\s+after\s+(?P<dependency>.+)$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build execution orchestration artifacts from an existing plan or task source."
    )
    parser.add_argument("--input", required=True, help="Path to the source plan or task artifact.")
    parser.add_argument(
        "--format",
        choices=("auto", "brief", "tasks", "checklist", "spec"),
        default="auto",
        help="Interpretation mode for the input source.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    parser.add_argument("--json-out", help="Optional explicit JSON output path.")
    parser.add_argument("--markdown-out", help="Optional explicit Markdown output path.")
    return parser.parse_args()


def detect_format(text: str, requested: str) -> str:
    if requested != "auto":
        return requested
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if any(line.startswith("- [") for line in lines):
        return "checklist"
    if any(line.startswith("- ") for line in lines):
        return "tasks"
    if any(line.startswith("#") for line in lines):
        return "spec"
    return "brief"


def normalize_title(raw: str) -> str:
    parts: list[str] = []
    for token in raw.split():
        if token.isupper():
            parts.append(token)
            continue
        if len(token) > 1 and token[0].isalpha():
            parts.append(token[0].upper() + token[1:])
        else:
            parts.append(token)
    return " ".join(parts).strip()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "work-item"


def parse_write_scopes(body: str) -> tuple[str, list[str]]:
    match = WRITES_PATTERN.search(body)
    if not match:
        return body.strip(), []
    writes = [item.strip() for item in match.group("writes").split(",") if item.strip()]
    trimmed = body[: match.start()].strip()
    return trimmed, writes


def parse_task_line(line: str) -> dict[str, object] | None:
    match = CHECKLIST_PATTERN.match(line.strip())
    if not match:
        return None
    body, writes = parse_write_scopes(match.group("body"))
    dependency_ref = None
    after_match = AFTER_PATTERN.match(body)
    if after_match:
        body = after_match.group("title").strip()
        dependency_ref = normalize_title(after_match.group("dependency").strip())
    title = normalize_title(body)
    task_id = slugify(title)
    verification = "Run the relevant targeted verification for this work item."
    if "test" in title.lower():
        verification = "Run the targeted tests covering this work item."
    return {
        "id": task_id,
        "title": title,
        "source_text": line.strip(),
        "status": "pending",
        "write_scope": writes,
        "dependency_ref": dependency_ref,
        "verification_expectation": verification,
        "notes": [],
    }


def parse_input(text: str) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        task = parse_task_line(line)
        if task:
            tasks.append(task)
    return tasks


def resolve_dependencies(work_items: list[dict[str, object]]) -> list[dict[str, str]]:
    title_to_id = {item["title"]: item["id"] for item in work_items}
    dependencies: list[dict[str, str]] = []
    for item in work_items:
        dependency_ref = item.pop("dependency_ref", None)
        if dependency_ref and dependency_ref in title_to_id:
            dependencies.append({"from": title_to_id[dependency_ref], "to": item["id"]})
    return dependencies


def build_batches(work_items: list[dict[str, object]], dependencies: list[dict[str, str]]) -> list[dict[str, object]]:
    item_map = {item["id"]: item for item in work_items}
    outgoing: dict[str, list[str]] = {item["id"]: [] for item in work_items}
    indegree: dict[str, int] = {item["id"]: 0 for item in work_items}
    for edge in dependencies:
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1

    ready = deque(sorted([item_id for item_id, count in indegree.items() if count == 0]))
    processed: set[str] = set()
    batches: list[dict[str, object]] = []
    batch_index = 1

    while ready:
        wave = list(ready)
        ready.clear()
        groups: list[list[str]] = []
        for item_id in wave:
            item_scope = set(item_map[item_id]["write_scope"])
            placed = False
            for group in groups:
                group_scope = set()
                for existing_id in group:
                    group_scope.update(item_map[existing_id]["write_scope"])
                if item_scope and group_scope and item_scope.intersection(group_scope):
                    continue
                group.append(item_id)
                placed = True
                break
            if not placed:
                groups.append([item_id])

        for group in groups:
            batches.append(
                {
                    "id": f"batch-{batch_index}",
                    "objective": "Execute ready work items with non-conflicting write scopes.",
                    "tasks": group,
                    "return_condition": "Return changed files, verification run, and open blockers for checkpoint review.",
                }
            )
            batch_index += 1

        for item_id in wave:
            processed.add(item_id)
            for neighbor in outgoing[item_id]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    ready.append(neighbor)
        ready = deque(sorted(ready))

    remaining = [item["id"] for item in work_items if item["id"] not in processed]
    for item_id in remaining:
        batches.append(
            {
                "id": f"batch-{batch_index}",
                "objective": "Review unresolved work item manually because dependency resolution remained incomplete.",
                "tasks": [item_id],
                "return_condition": "Resolve the dependency ambiguity before more parallel work starts.",
            }
        )
        batch_index += 1

    return batches


def build_blocked_items(work_items: list[dict[str, object]], dependencies: list[dict[str, str]]) -> list[dict[str, object]]:
    blocked_by: dict[str, list[str]] = {}
    for edge in dependencies:
        blocked_by.setdefault(edge["to"], []).append(edge["from"])
    results: list[dict[str, object]] = []
    for item in work_items:
        if item["id"] in blocked_by:
            results.append({"id": item["id"], "blocked_by": blocked_by[item["id"]]})
    return results


def build_checkpoint_sequence(batches: list[dict[str, object]]) -> list[dict[str, object]]:
    checkpoints: list[dict[str, object]] = []
    for index, batch in enumerate(batches, start=1):
        checkpoints.append(
            {
                "id": f"checkpoint-{index}",
                "after_batch": batch["id"],
                "questions": [
                    "What completed?",
                    "What drifted out of scope?",
                    "What verification ran?",
                    "What new blockers appeared?",
                    "Do the remaining batches still have valid assumptions?",
                ],
            }
        )
    return checkpoints


def build_payload(source_path: Path, detected_format: str, work_items: list[dict[str, object]]) -> dict[str, object]:
    dependencies = resolve_dependencies(work_items)
    batches = build_batches(work_items, dependencies)
    checkpoints = build_checkpoint_sequence(batches)
    blocked_items = build_blocked_items(work_items, dependencies)
    merge_points = [{"batch": batch["id"], "checkpoint": checkpoint["id"]} for batch, checkpoint in zip(batches, checkpoints)]
    return {
        "input_summary": {
            "source_path": str(source_path),
            "format": detected_format,
            "work_item_count": len(work_items),
        },
        "work_items": work_items,
        "dependencies": dependencies,
        "blocked_items": blocked_items,
        "parallel_batches": batches,
        "main_thread_duties": [
            "Own critical-path blockers and dependency clarification.",
            "Review each checkpoint before launching the next wave.",
            "Handle integration, merge conflicts, and final verification.",
        ],
        "merge_points": merge_points,
        "checkpoint_sequence": checkpoints,
        "assumptions": [
            "Dependency extraction relies on explicit 'after ...' phrases in the source text.",
            "Write-scope conflicts are inferred from exact scope-string overlap.",
        ],
        "risks": [
            "Hidden shared files can still reduce the safety of parallel batches.",
            "Freeform input may omit dependencies that require manual correction.",
        ],
        "verification_boundaries": [
            "Generated artifacts describe expected verification; they do not prove commands were run.",
            "Later waves remain provisional until checkpoint review confirms the assumptions still hold.",
        ],
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Execution Orchestration Report")
    lines.append("")
    lines.append("## Input Summary")
    lines.append("")
    lines.append(f"- Source: `{payload['input_summary']['source_path']}`")
    lines.append(f"- Format: `{payload['input_summary']['format']}`")
    lines.append(f"- Work items: `{payload['input_summary']['work_item_count']}`")
    lines.append("")
    lines.append("## Execution Units")
    lines.append("")
    for item in payload["work_items"]:
        scope = ", ".join(item["write_scope"]) if item["write_scope"] else "unspecified"
        lines.append(f"- `{item['id']}`: {item['title']} (writes: {scope})")
    lines.append("")
    lines.append("## Dependency Summary")
    lines.append("")
    if payload["dependencies"]:
        for edge in payload["dependencies"]:
            lines.append(f"- `{edge['from']}` -> `{edge['to']}`")
    else:
        lines.append("- No explicit dependencies were detected.")
    lines.append("")
    lines.append("## Parallel Batches")
    lines.append("")
    for batch in payload["parallel_batches"]:
        lines.append(f"### {batch['id']}")
        lines.append(f"- Objective: {batch['objective']}")
        lines.append(f"- Tasks: {', '.join(f'`{task}`' for task in batch['tasks'])}")
        lines.append(f"- Return condition: {batch['return_condition']}")
        lines.append("")
    lines.append("## Main-Thread Duties")
    lines.append("")
    for duty in payload["main_thread_duties"]:
        lines.append(f"- {duty}")
    lines.append("")
    lines.append("## Checkpoints")
    lines.append("")
    for checkpoint in payload["checkpoint_sequence"]:
        lines.append(f"### {checkpoint['id']}")
        lines.append(f"- After batch: `{checkpoint['after_batch']}`")
        for question in checkpoint["questions"]:
            lines.append(f"- {question}")
        lines.append("")
    lines.append("## Risks And Blockers")
    lines.append("")
    if payload["blocked_items"]:
        for blocked in payload["blocked_items"]:
            blockers = ", ".join(f'`{item}`' for item in blocked["blocked_by"])
            lines.append(f"- `{blocked['id']}` is blocked by {blockers}")
    else:
        lines.append("- No currently blocked items were detected.")
    for risk in payload["risks"]:
        lines.append(f"- Risk: {risk}")
    lines.append("")
    lines.append("## Verification Boundaries")
    lines.append("")
    for boundary in payload["verification_boundaries"]:
        lines.append(f"- {boundary}")
    lines.append("")
    return "\n".join(lines)


def ensure_output_path(path_value: str | None, output_dir: Path, filename: str) -> Path:
    if path_value:
        return Path(path_value)
    return output_dir / filename


def main() -> None:
    args = parse_args()
    source_path = Path(args.input)
    text = source_path.read_text(encoding="utf-8")
    detected_format = detect_format(text, args.format)
    work_items = parse_input(text)
    if not work_items:
        raise SystemExit("No work items could be extracted from the input.")
    payload = build_payload(source_path, detected_format, work_items)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = ensure_output_path(args.json_out, output_dir, "execution-orchestration.json")
    markdown_path = ensure_output_path(args.markdown_out, output_dir, "execution-orchestration.md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_path}")
    print(f"JSON_OUT={json_path}")


if __name__ == "__main__":
    main()
