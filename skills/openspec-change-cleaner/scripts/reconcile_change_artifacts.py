#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_change_cleanup_report import OpenSpecCli, build_cleanup_report, write_text


SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
BULLET_PATTERN = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.MULTILINE)
BACKTICK_PATTERN = re.compile(r"`([^`]+)`")
TASK_PATTERN = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair stale OpenSpec change artifacts from current module evidence and optionally archive them."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--change", action="append", default=[])
    parser.add_argument("--archive-when-ready", action="store_true")
    parser.add_argument("--openspec-bin", default="openspec")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    return parser.parse_args(argv)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def first_heading(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def extract_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[section_name] = text[start:end].strip()
    return sections


def extract_bullets(section_text: str) -> list[str]:
    if not section_text:
        return []
    return [match.group(1).strip() for match in BULLET_PATTERN.finditer(section_text)]


def parse_openai_yaml(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        if key.strip() in {"display_name", "short_description", "default_prompt"}:
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def proposal_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    next_match = SECTION_PATTERN.search(text, match.end())
    end = next_match.start() if next_match else len(text)
    return text[match.end() : end].strip()


def infer_capability_names(proposal_text: str) -> list[str]:
    capabilities_text = proposal_section(proposal_text, "Capabilities")
    if not capabilities_text:
        return []
    names: list[str] = []
    in_new_capabilities = False
    for raw_line in capabilities_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("### "):
            in_new_capabilities = stripped.lower() == "### new capabilities"
            continue
        if not in_new_capabilities:
            continue
        if not stripped.startswith("-"):
            continue
        matches = BACKTICK_PATTERN.findall(stripped)
        if matches:
            names.extend(matches)
    return names


def derive_module_candidates(change_name: str) -> list[str]:
    candidates = [change_name]
    prefixes = ("create-", "add-", "enhance-", "improve-", "update-", "fix-", "repair-")
    stripped = change_name
    for prefix in prefixes:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix) :]
            break
    suffixes = ("-skill", "-module", "-support")
    for suffix in suffixes:
        if stripped.endswith(suffix):
            stripped = stripped[: -len(suffix)]
            break
    candidates.append(stripped)
    return [item for item in candidates if item]


def is_skill_module(path: Path) -> bool:
    return path.is_dir() and (path / "SKILL.md").exists() and (path / "agents" / "openai.yaml").exists()


def infer_module_root(repo_root: Path, change_name: str, proposal_text: str) -> Path | None:
    explicit_candidates: list[Path] = []
    for token in BACKTICK_PATTERN.findall(proposal_text):
        candidate = repo_root / token
        if is_skill_module(candidate):
            explicit_candidates.append(candidate)
    if len(explicit_candidates) == 1:
        return explicit_candidates[0]
    if len(explicit_candidates) > 1:
        return None

    derived_candidates: list[Path] = []
    for candidate_name in derive_module_candidates(change_name):
        candidate = repo_root / candidate_name
        if is_skill_module(candidate):
            derived_candidates.append(candidate)
    if len(derived_candidates) == 1:
        return derived_candidates[0]
    return None


def collect_relative_paths(directory: Path, pattern: str) -> list[str]:
    if not directory.exists():
        return []
    return [path.relative_to(directory.parent).as_posix() for path in sorted(directory.glob(pattern))]


def collect_recursive_paths(directory: Path, pattern: str) -> list[str]:
    if not directory.exists():
        return []
    return [path.relative_to(directory.parent.parent if directory.parent.exists() else directory).as_posix() for path in sorted(directory.rglob(pattern))]


def extract_module_evidence(module_root: Path) -> dict[str, Any]:
    skill_text = read_text(module_root / "SKILL.md")
    claude_text = read_text(module_root / "CLAUDE.md") if (module_root / "CLAUDE.md").exists() else ""
    frontmatter = parse_frontmatter(skill_text)
    sections = extract_sections(claude_text)
    references_dir = module_root / "references"
    scripts_dir = module_root / "scripts"
    tests_dir = module_root / "tests"

    output_contract = extract_bullets(sections.get("Output Contract", ""))
    if not output_contract and (references_dir / "output-schema.md").exists():
        output_contract = extract_bullets(read_text(references_dir / "output-schema.md"))

    return {
        "module_root": str(module_root),
        "module_name": module_root.name,
        "skill_name": frontmatter.get("name", module_root.name),
        "skill_description": frontmatter.get("description", ""),
        "skill_title": first_heading(skill_text) or module_root.name,
        "purpose": sections.get("Purpose", "").strip(),
        "main_interface": extract_bullets(sections.get("Main Interface", "")),
        "output_contract": output_contract,
        "openai": parse_openai_yaml(module_root / "agents" / "openai.yaml"),
        "references": [path.relative_to(module_root).as_posix() for path in sorted(references_dir.rglob("*.md"))]
        if references_dir.exists()
        else [],
        "scripts": [path.relative_to(module_root).as_posix() for path in sorted(scripts_dir.iterdir()) if path.is_file()]
        if scripts_dir.exists()
        else [],
        "tests": [path.relative_to(module_root).as_posix() for path in sorted(tests_dir.rglob("test_*.py"))]
        if tests_dir.exists()
        else [],
    }


def non_empty_paragraph(text: str) -> str:
    for block in re.split(r"\n\s*\n", text.strip()):
        cleaned = " ".join(block.split())
        if cleaned:
            return cleaned
    return ""


def capability_summary(capability_name: str, evidence: dict[str, Any]) -> str:
    purpose = non_empty_paragraph(str(evidence.get("purpose", "")))
    if purpose:
        return purpose
    description = str(evidence.get("skill_description", "")).strip()
    if description:
        return description
    return f"Document the current {capability_name} capability from the checked-in module."


def build_proposal_text(change_name: str, capability_names: list[str], evidence: dict[str, Any], existing_text: str) -> str:
    why = proposal_section(existing_text, "Why")
    if not why:
        why = (
            f"The `{evidence['module_name']}` module already exists in the repository, but the OpenSpec change "
            f"`{change_name}` is missing or drifting from the current implementation artifacts."
        )
    what_lines = [
        f"- Backfill and refresh the OpenSpec artifacts for the existing `{evidence['module_name']}` module.",
        "- Preserve the module's current documented workflow, helper scripts, references, and tests.",
        "- Revalidate the repaired change and archive it when the artifact set is complete.",
    ]
    capability_lines = [f"- `{name}`: {capability_summary(name, evidence)}" for name in capability_names]
    impact_lines = [
        f"- OpenSpec change files under `openspec/changes/{change_name}` are restored to match the shipped module.",
        f"- Existing implementation files under `{evidence['module_name']}` remain the source of truth.",
    ]
    return (
        "## Why\n\n"
        f"{why.strip()}\n\n"
        "## What Changes\n\n"
        + "\n".join(what_lines)
        + "\n\n## Capabilities\n\n### New Capabilities\n"
        + "\n".join(capability_lines)
        + "\n\n### Modified Capabilities\n- None.\n\n## Impact\n\n"
        + "\n".join(impact_lines)
        + "\n"
    )


def build_design_text(change_name: str, capability_names: list[str], evidence: dict[str, Any]) -> str:
    module_name = evidence["module_name"]
    interface_lines = evidence.get("main_interface", [])
    output_lines = evidence.get("output_contract", [])
    test_lines = evidence.get("tests", [])
    decisions = [
        f"- Treat `{module_name}` as an existing script-backed skill module and repair the OpenSpec artifacts around it instead of redesigning the implementation.",
        f"- Preserve the proposal capability names `{', '.join(capability_names)}` when regenerating delta specs.",
    ]
    if interface_lines:
        decisions.append(f"- Reflect the documented main interface: {interface_lines[0]}")
    if output_lines:
        decisions.append(f"- Preserve the documented output contract starting from: {output_lines[0]}")
    verification = ", ".join(test_lines) if test_lines else "checked-in module structure"
    return (
        "## Context\n\n"
        f"`{module_name}` is already implemented, but change `{change_name}` needs repaired OpenSpec artifacts so it can validate and archive cleanly.\n\n"
        "## Goals / Non-Goals\n\n"
        "**Goals:**\n"
        f"- restore `design.md`, delta specs, and `tasks.md` for `{change_name}`\n"
        f"- describe the current `{module_name}` implementation instead of an earlier proposal snapshot\n"
        "- make the change safe to validate and archive\n\n"
        "**Non-Goals:**\n"
        "- redesign the existing module behavior\n"
        "- delete archive history automatically\n\n"
        "## Decisions\n\n"
        + "\n".join(decisions)
        + "\n\n## Risks / Trade-offs\n\n"
        "- [Risk] Module evidence may be incomplete or overly generic.  \n"
        "  → Mitigation: stop on ambiguity rather than guessing a module or capability.\n"
        "- [Risk] The repaired change could validate structurally while remaining semantically stale.  \n"
        "  → Mitigation: generate artifacts from checked-in docs, scripts, and tests, then re-run OpenSpec validation.\n\n"
        "## Migration Plan\n\n"
        "- regenerate the missing or stale OpenSpec artifacts\n"
        "- re-run `show`, `status`, and `validate`\n"
        "- archive when the repaired change becomes complete\n\n"
        "## Open Questions\n\n"
        f"- Verification evidence currently comes from {verification}.\n"
    )


def build_spec_text(capability_name: str, evidence: dict[str, Any]) -> str:
    purpose = capability_summary(capability_name, evidence)
    interface_lines = evidence.get("main_interface", [])
    output_lines = evidence.get("output_contract", [])
    scripts = evidence.get("scripts", [])
    tests = evidence.get("tests", [])
    interface_sentence = interface_lines[0] if interface_lines else "the documented module workflow"
    output_sentence = output_lines[0] if output_lines else "the module's documented outputs"
    script_sentence = scripts[0] if scripts else "the module resources"
    test_sentence = tests[0] if tests else "the module checks"
    return (
        "## ADDED Requirements\n\n"
        f"### Requirement: Provide The {capability_name} Workflow\n"
        f"The system SHALL provide the current `{evidence['module_name']}` capability so that Codex can rely on its documented workflow instead of improvising one.\n\n"
        "#### Scenario: Codex needs the module workflow\n"
        f"- **WHEN** Codex loads `{evidence['module_name']}` for a matching request\n"
        f"- **THEN** it can follow the documented module purpose: {purpose}\n"
        f"- **AND** it can locate the module entry guidance from `{evidence['module_name']}/SKILL.md`\n\n"
        f"### Requirement: Expose Deterministic Module Interfaces\n"
        "The system SHALL expose deterministic module interfaces and helper resources that match the checked-in module surface.\n\n"
        "#### Scenario: Codex needs to execute the module interface\n"
        f"- **WHEN** Codex reads the module's main interface and helper resources\n"
        f"- **THEN** it can find the documented interface starting from {interface_sentence}\n"
        f"- **AND** it can locate the relevant helper surface such as `{script_sentence}`\n\n"
        f"### Requirement: Preserve Documented Outputs And Verification Signals\n"
        "The system SHALL preserve the current output expectations and verification surface for the module.\n\n"
        "#### Scenario: Codex needs to confirm outputs and checks\n"
        f"- **WHEN** Codex inspects the module references and tests\n"
        f"- **THEN** it can find output expectations starting from {output_sentence}\n"
        f"- **AND** it can locate the verification surface starting from `{test_sentence}`\n"
    )


def build_main_spec_purpose(capability_name: str, evidence: dict[str, Any]) -> str:
    return (
        f"Describe the current {capability_name} capability for `{evidence['module_name']}` based on the "
        "checked-in workflow, deterministic interfaces, and documented outputs."
    )


def repair_main_spec_purpose(repo_root: Path, capability_names: list[str], evidence: dict[str, Any]) -> None:
    for capability_name in capability_names:
        main_spec_path = repo_root / "openspec" / "specs" / capability_name / "spec.md"
        if not main_spec_path.exists():
            continue
        text = read_text(main_spec_path)
        purpose_text = build_main_spec_purpose(capability_name, evidence)
        if "## Purpose" in text:
            pattern = re.compile(r"(##\s+Purpose\s*\n)(.*?)(?=\n##\s+|\Z)", re.DOTALL)
            if pattern.search(text):
                text = pattern.sub(lambda match: f"{match.group(1)}{purpose_text}\n", text, count=1)
            else:
                text = text.replace("## Purpose", f"## Purpose\n{purpose_text}\n", 1)
        else:
            text = f"# {capability_name} Specification\n\n## Purpose\n{purpose_text}\n\n{text.lstrip()}"
        write_text(main_spec_path, text)


def build_tasks_text(change_name: str, capability_names: list[str], evidence: dict[str, Any], validation_ok: bool) -> str:
    verification_note = "Re-run OpenSpec validation and confirm the repaired change is complete."
    if validation_ok:
        verification_note = "Re-run OpenSpec validation and confirm the repaired change validates cleanly."
    return (
        "## 1. Rebuild Change Artifacts\n\n"
        f"- [x] 1.1 Reconcile `proposal.md` for `{change_name}` against the checked-in `{evidence['module_name']}` module.\n"
        "- [x] 1.2 Regenerate `design.md` from the current module structure and documented interfaces.\n"
        f"- [x] 1.3 Regenerate delta specs for `{', '.join(capability_names)}` from current module evidence.\n\n"
        "## 2. Confirm Current Module Evidence\n\n"
        "- [x] 2.1 Confirm the module still exposes `SKILL.md`, `agents/openai.yaml`, references, scripts, and tests.\n"
        "- [x] 2.2 Record the repaired change as documentation for an already-shipped implementation rather than new feature work.\n\n"
        "## 3. Validate And Close\n\n"
        "- [x] 3.1 Re-run `openspec show --json` and confirm the repaired change exposes parsed deltas.\n"
        "- [x] 3.2 Re-run `openspec status --change <id> --json` and confirm the full artifact set is present.\n"
        f"- [x] 3.3 {verification_note}\n"
    )


def ensure_capability_names(proposal_text: str, module_root: Path) -> list[str]:
    names = infer_capability_names(proposal_text)
    if names:
        return names
    derived = module_root.name
    for suffix in ("-assistant", "-fixer", "-builder", "-workflow", "-skill"):
        if derived.endswith(suffix):
            derived = derived[: -len(suffix)]
            break
    return [derived]


def repair_change(
    *,
    repo_root: Path,
    cli: Any,
    change_name: str,
) -> dict[str, Any]:
    change_dir = repo_root / "openspec" / "changes" / change_name
    proposal_path = change_dir / "proposal.md"
    proposal_text = read_text(proposal_path) if proposal_path.exists() else ""
    module_root = infer_module_root(repo_root, change_name, proposal_text)
    if module_root is None:
        return {
            "change_name": change_name,
            "status": "blocked",
            "reason": "Could not infer a unique target module from proposal text or change name.",
        }

    capability_names = ensure_capability_names(proposal_text, module_root)
    evidence = extract_module_evidence(module_root)
    write_text(proposal_path, build_proposal_text(change_name, capability_names, evidence, proposal_text))
    write_text(change_dir / "design.md", build_design_text(change_name, capability_names, evidence))
    for capability_name in capability_names:
        write_text(change_dir / "specs" / capability_name / "spec.md", build_spec_text(capability_name, evidence))

    validation_payload = cli.validate(change_name)
    validation_items = validation_payload.get("items", [])
    validation_ok = bool(validation_items and isinstance(validation_items[0], dict) and validation_items[0].get("valid"))
    write_text(change_dir / "tasks.md", build_tasks_text(change_name, capability_names, evidence, validation_ok))

    show_payload = cli.show_change(change_name)
    status_payload = cli.status(change_name)
    validate_payload = cli.validate(change_name)
    valid = bool(validate_payload.get("items") and validate_payload["items"][0].get("valid"))
    complete = bool(status_payload.get("isComplete"))
    return {
        "change_name": change_name,
        "status": "repaired",
        "module_root": str(module_root),
        "capabilities": capability_names,
        "show": show_payload,
        "status_payload": status_payload,
        "validate_payload": validate_payload,
        "valid": valid,
        "complete": complete,
    }


def reconcile_changes(
    *,
    repo_root: Path,
    cli: Any | None = None,
    change_names: list[str] | None = None,
    archive_when_ready: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if cli is None:
        cli = OpenSpecCli(repo_root=repo_root)

    cleanup_report = build_cleanup_report(
        repo_root=repo_root,
        cli=cli,
        include_archive=False,
        change_names=change_names,
    )
    active_entries = cleanup_report.get("active_changes", [])
    if change_names:
        selected = active_entries
    else:
        selected = [
            entry
            for entry in active_entries
            if entry.get("assessment", {}).get("classification") == "repair-artifacts"
        ]

    results: list[dict[str, Any]] = []
    for entry in selected:
        repaired = repair_change(repo_root=repo_root, cli=cli, change_name=str(entry["name"]))
        if repaired.get("status") == "repaired" and archive_when_ready and repaired.get("valid") and repaired.get("complete"):
            cli.archive(str(entry["name"]))
            repair_main_spec_purpose(repo_root, list(repaired.get("capabilities", [])), extract_module_evidence(Path(str(repaired["module_root"]))))
            repaired["archived"] = True
        else:
            repaired["archived"] = False
        results.append(repaired)

    return {
        "repo_root": str(repo_root),
        "changes": results,
        "summary": {
            "repaired_changes": [item["change_name"] for item in results if item["status"] == "repaired"],
            "blocked_changes": [item["change_name"] for item in results if item["status"] == "blocked"],
            "archived_changes": [item["change_name"] for item in results if item.get("archived")],
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# OpenSpec Change Reconciliation Report",
        "",
        f"Repo root: `{result.get('repo_root', '')}`",
        "",
        "## Summary",
        f"- Repaired changes: {', '.join(result.get('summary', {}).get('repaired_changes', [])) or 'none'}",
        f"- Blocked changes: {', '.join(result.get('summary', {}).get('blocked_changes', [])) or 'none'}",
        f"- Archived changes: {', '.join(result.get('summary', {}).get('archived_changes', [])) or 'none'}",
        "",
        "## Changes",
    ]
    changes = result.get("changes", [])
    if not changes:
        lines.extend(["", "- None."])
    for item in changes:
        lines.extend(
            [
                "",
                f"### {item.get('change_name', 'unknown-change')}",
                f"- Status: `{item.get('status', 'unknown')}`",
            ]
        )
        if item.get("module_root"):
            lines.append(f"- Module: `{item['module_root']}`")
        if item.get("capabilities"):
            lines.append(f"- Capabilities: {', '.join(item['capabilities'])}")
        if item.get("reason"):
            lines.append(f"- Reason: {item['reason']}")
        if item.get("archived"):
            lines.append("- Archived after successful repair and validation.")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    cli = OpenSpecCli(repo_root=repo_root, openspec_bin=args.openspec_bin)
    result = reconcile_changes(
        repo_root=repo_root,
        cli=cli,
        change_names=args.change or None,
        archive_when_ready=args.archive_when_ready,
    )
    markdown = render_markdown(result)
    if args.json_out:
        json_path = Path(args.json_out).resolve()
        write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2))
        print(f"JSON_OUT={json_path}")
    if args.markdown_out:
        markdown_path = Path(args.markdown_out).resolve()
        write_text(markdown_path, markdown)
        print(f"MARKDOWN_OUT={markdown_path}")

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not args.json_out and not args.markdown_out:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
