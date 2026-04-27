from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    ".uv-cache",
    ".uv-cache-codex",
    ".uv-cache-local",
    ".codex-uv-cache",
    ".uv-python",
    "tmp",
    "_tmp",
}
ALLOWED_HIDDEN_DIRS = {".github", ".husky"}
DOC_EXTENSIONS = {".md", ".markdown", ".rst", ".txt"}
MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pnpm-lock.yaml",
    "bun.lockb",
    "requirements.txt",
}


@dataclass
class Opportunity:
    title: str
    category: str
    impact: int
    urgency: int
    confidence: int
    effort: int
    rationale: str
    evidence: list[str]
    next_action: str

    @property
    def score(self) -> int:
        return self.impact * 3 + self.urgency * 2 + self.confidence * 2 - self.effort

    @property
    def priority(self) -> str:
        if self.score >= 20:
            return "high"
        if self.score >= 13:
            return "medium"
        return "low"

    def to_dict(self, index: int) -> dict[str, object]:
        return {
            "id": f"opp-{index:03d}",
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "score": self.score,
            "impact": self.impact,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "effort": self.effort,
            "rationale": self.rationale,
            "evidence": [{"path": p} for p in self.evidence],
            "recommended_next_action": self.next_action,
        }


def normalize_rel(path_text: str) -> str:
    return path_text.replace("\\", "/").strip("/")


def has_prefix(path: str, prefixes: Iterable[str]) -> bool:
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def is_doc(path: str) -> bool:
    lower = path.lower()
    if Path(lower).suffix in DOC_EXTENSIONS:
        return True
    return lower.endswith("readme") or lower.endswith("readme.md")


def discover_files(root: Path) -> list[str]:
    results: list[str] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        parts = file_path.relative_to(root).parts
        if any(
            part in SKIP_DIR_NAMES
            or part.startswith("_tmp")
            or (part.startswith(".") and part not in ALLOWED_HIDDEN_DIRS)
            for part in parts[:-1]
        ):
            continue
        results.append(normalize_rel(str(file_path.relative_to(root))))
    return sorted(results)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a repository optimization opportunity report")
    parser.add_argument("--root", required=True, help="Repository root to analyze")
    parser.add_argument("--target", help="Optional target path prefix")
    parser.add_argument("--doc", action="append", default=[], help="Explicit doc path to include")
    parser.add_argument("--markdown-out", help="Markdown output path")
    parser.add_argument("--json-out", help="JSON output path")
    parser.add_argument("--include", action="append", default=[], help="Path prefix include filter")
    parser.add_argument("--exclude", action="append", default=[], help="Path prefix exclude filter")
    parser.add_argument("--focus", default="", help="Focus keyword")
    parser.add_argument("--max-files", type=int, default=200, help="Max surface files")
    parser.add_argument("--max-docs", type=int, default=40, help="Max discovered docs")
    parser.add_argument("--top", type=int, default=10, help="Top backlog size")
    return parser.parse_args()


def load_command_signals(root: Path, all_files: list[str]) -> list[str]:
    signals: list[str] = []
    for rel in all_files:
        name = Path(rel).name
        if name == "package.json":
            try:
                payload = json.loads((root / rel).read_text(encoding="utf-8"))
            except Exception:
                continue
            scripts = payload.get("scripts") if isinstance(payload, dict) else None
            if isinstance(scripts, dict):
                for key in scripts.keys():
                    if isinstance(key, str):
                        signals.append(f"npm-script:{key}")
        elif name in {"pyproject.toml", "Cargo.toml", "go.mod"}:
            signals.append(f"manifest:{name}")
    return sorted(set(signals))


def build_opportunities(
    surface_paths: list[str],
    discovered_docs: list[dict[str, str]],
    command_signals: list[str],
    focus: str,
) -> list[dict[str, object]]:
    docs = [entry["path"] for entry in discovered_docs]
    route_files = [p for p in surface_paths if "/routes/" in p or "/route" in p]
    service_files = [p for p in surface_paths if "/service" in p or "/services/" in p]
    repo_files = [p for p in surface_paths if "/repository" in p or "/repositories/" in p]
    test_files = [p for p in surface_paths if "/tests/" in p or Path(p).name.startswith("test_")]

    opportunities: list[Opportunity] = []

    if route_files and service_files:
        evidence = (route_files + service_files + repo_files)[:4]
        opportunities.append(
            Opportunity(
                title="Clarify route-to-service boundaries",
                category="architecture",
                impact=5,
                urgency=4,
                confidence=4,
                effort=2,
                rationale="Routes and services are both present; explicit contracts reduce coupling and hidden regressions.",
                evidence=evidence,
                next_action="Map request flow and define stable interfaces between route handlers and service layer.",
            )
        )

    if not test_files:
        evidence = surface_paths[:3] or ["(no surface files)"]
        opportunities.append(
            Opportunity(
                title="Backfill regression tests for active surface",
                category="testing",
                impact=5,
                urgency=4,
                confidence=4,
                effort=3,
                rationale="Current surface lacks explicit tests, increasing risk during iterative changes.",
                evidence=evidence,
                next_action="Add scoped tests covering the highest-risk paths before additional refactors.",
            )
        )

    if docs:
        opportunities.append(
            Opportunity(
                title="Align implementation with roadmap/spec artifacts",
                category="documentation",
                impact=4,
                urgency=3,
                confidence=4,
                effort=2,
                rationale="Planning documents exist and should be reconciled against active implementation seams.",
                evidence=docs[:4],
                next_action="Review doc requirements against current code paths and track confirmed gaps.",
            )
        )

    has_test_signal = any("test" in signal for signal in command_signals)
    has_lint_signal = any("lint" in signal for signal in command_signals)
    if command_signals and (not has_test_signal or not has_lint_signal):
        opportunities.append(
            Opportunity(
                title="Strengthen local verification command surface",
                category="verification",
                impact=4,
                urgency=3,
                confidence=3,
                effort=2,
                rationale="Manifest commands are present but verification coverage appears incomplete for iterative delivery.",
                evidence=command_signals[:5],
                next_action="Standardize lint/test/build commands and document execution order for contributors.",
            )
        )

    if focus:
        opportunities.append(
            Opportunity(
                title=f"Create focused optimization track for `{focus}`",
                category="workflow",
                impact=3,
                urgency=3,
                confidence=4,
                effort=1,
                rationale="A focus keyword was provided; converting it into a scoped track speeds execution and verification.",
                evidence=[focus],
                next_action="Run a narrowed follow-up audit around the focus area and track outcomes separately.",
            )
        )

    if not opportunities:
        opportunities.append(
            Opportunity(
                title="Establish baseline optimization backlog",
                category="maintainability",
                impact=3,
                urgency=2,
                confidence=3,
                effort=1,
                rationale="Repository scan completed with limited direct signals; baseline backlog keeps next actions explicit.",
                evidence=surface_paths[:3] or ["(empty-repo)"],
                next_action="Increase signal by adding architecture notes, test inventory, and command documentation.",
            )
        )

    records = [item.to_dict(i + 1) for i, item in enumerate(opportunities)]
    records.sort(key=lambda item: int(item["score"]), reverse=True)
    return records


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Invalid root path: {root}")

    target_prefix = normalize_rel(args.target) if args.target else ""
    include_prefixes = [normalize_rel(item) for item in args.include if normalize_rel(item)]
    exclude_prefixes = [normalize_rel(item) for item in args.exclude if normalize_rel(item)]

    all_files = discover_files(root)

    filtered: list[str] = []
    for rel in all_files:
        if target_prefix and not has_prefix(rel, [target_prefix]):
            continue
        if include_prefixes and not has_prefix(rel, include_prefixes):
            continue
        if exclude_prefixes and has_prefix(rel, exclude_prefixes):
            continue
        filtered.append(rel)

    limits: list[dict[str, object]] = []

    surface_paths = [rel for rel in filtered if not is_doc(rel)]
    if args.max_files and len(surface_paths) > args.max_files:
        limits.append(
            {
                "kind": "max-files",
                "requested": args.max_files,
                "dropped": len(surface_paths) - args.max_files,
            }
        )
        surface_paths = surface_paths[: args.max_files]

    discovered_docs: list[dict[str, str]] = []
    seen_docs: set[str] = set()

    for doc_rel in args.doc:
        rel = normalize_rel(doc_rel)
        if not rel:
            continue
        path = root / rel
        if path.exists() and path.is_file() and rel not in seen_docs:
            discovered_docs.append({"path": rel, "source": "explicit-doc"})
            seen_docs.add(rel)

    auto_doc_pool = [rel for rel in filtered if is_doc(rel)]
    for rel in auto_doc_pool:
        if rel in seen_docs:
            continue
        discovered_docs.append({"path": rel, "source": "discovered"})
        seen_docs.add(rel)

    if args.max_docs and len(discovered_docs) > args.max_docs:
        limits.append(
            {
                "kind": "max-docs",
                "requested": args.max_docs,
                "dropped": len(discovered_docs) - args.max_docs,
            }
        )
        discovered_docs = discovered_docs[: args.max_docs]

    command_signals = load_command_signals(root, all_files)

    opportunities = build_opportunities(surface_paths, discovered_docs, command_signals, args.focus)
    top_backlog = opportunities[: max(args.top, 0)] if args.top else opportunities

    category_buckets: dict[str, list[int]] = defaultdict(list)
    for opp in opportunities:
        category_buckets[str(opp["category"])].append(int(opp["score"]))

    category_summary = {
        category: {
            "count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
        }
        for category, scores in category_buckets.items()
    }

    linked_skills: list[dict[str, str]] = [
        {
            "skill": "project-architecture-design-analyzer",
            "reason": "Use for deeper architecture seam and boundary analysis.",
        }
    ]

    doc_signal = any(
        token in entry["path"].lower() for entry in discovered_docs for token in ("spec", "plan", "roadmap", "requirement")
    )
    if discovered_docs or doc_signal:
        linked_skills.append(
            {
                "skill": "feature-gap-requirements-auditor",
                "reason": "Use to reconcile planning docs with implementation status on scoped features.",
            }
        )

    if command_signals:
        linked_skills.append(
            {
                "skill": "build-project-fixer",
                "reason": "Use to validate and harden lint/test/build command surfaces discovered in manifests.",
            }
        )

    blind_spots: list[str] = []
    if not discovered_docs:
        blind_spots.append("No planning docs were discovered in the current scope.")
    if not command_signals:
        blind_spots.append("No explicit command signals were extracted from manifests.")
    if target_prefix:
        blind_spots.append(f"Analysis constrained to target prefix `{target_prefix}`.")

    evidence_sources = {
        "surface_files": len(surface_paths),
        "discovered_docs": len(discovered_docs),
        "command_signals": len(command_signals),
    }

    payload = {
        "request": {
            "root": str(root),
            "target": args.target or "",
            "focus": args.focus,
            "include": include_prefixes,
            "exclude": exclude_prefixes,
            "docs": [normalize_rel(d) for d in args.doc],
            "top": args.top,
        },
        "repository_snapshot": {
            "root": str(root),
            "indexed_files": len(all_files),
            "surface_files": len(surface_paths),
            "doc_files": len(discovered_docs),
            "manifest_files": len([rel for rel in all_files if Path(rel).name in MANIFEST_NAMES]),
        },
        "surface_records": [{"path": rel, "kind": "surface"} for rel in surface_paths],
        "discovered_docs": discovered_docs,
        "evidence_sources": evidence_sources,
        "opportunities": opportunities,
        "top_backlog": top_backlog,
        "category_summary": category_summary,
        "linked_skills": linked_skills,
        "suggested_next_reads": [entry["path"] for entry in discovered_docs[:5]],
        "blind_spots": blind_spots,
        "limits": limits,
    }

    markdown_lines = [
        "# Project Optimization Opportunity Report",
        "",
        "## Request",
        f"- Root: `{payload['request']['root']}`",
        f"- Target: `{payload['request']['target'] or '(none)'}`",
        f"- Focus: `{payload['request']['focus'] or '(none)'}`",
        "",
        "## Repository Snapshot",
        f"- Indexed files: {payload['repository_snapshot']['indexed_files']}",
        f"- Surface files: {payload['repository_snapshot']['surface_files']}",
        f"- Doc files: {payload['repository_snapshot']['doc_files']}",
        "",
        "## Evidence Sources",
        f"- Surface records: {evidence_sources['surface_files']}",
        f"- Discovered docs: {evidence_sources['discovered_docs']}",
        f"- Command signals: {evidence_sources['command_signals']}",
        "",
        "## Optimization Opportunities",
    ]

    for opp in opportunities:
        markdown_lines.extend(
            [
                f"- **[{opp['priority']}] {opp['title']}** ({opp['category']}, score={opp['score']})",
                f"  - Rationale: {opp['rationale']}",
                f"  - Next action: {opp['recommended_next_action']}",
            ]
        )

    markdown_lines.extend(["", "## Top Backlog"])
    for opp in top_backlog:
        markdown_lines.append(f"- `{opp['id']}` {opp['title']} ({opp['priority']}, score={opp['score']})")

    markdown_lines.extend(["", "## Category Summary"])
    for category, summary in category_summary.items():
        markdown_lines.append(
            f"- {category}: count={summary['count']}, avg_score={summary['avg_score']}, max_score={summary['max_score']}"
        )

    markdown_lines.extend(["", "## Linked Skills"])
    for item in linked_skills:
        markdown_lines.append(f"- {item['skill']}: {item['reason']}")

    markdown_lines.extend(["", "## Suggested Next Reads"])
    if payload["suggested_next_reads"]:
        for path in payload["suggested_next_reads"]:
            markdown_lines.append(f"- {path}")
    else:
        markdown_lines.append("- (none)")

    markdown_lines.extend(["", "## Blind Spots"])
    if blind_spots:
        for item in blind_spots:
            markdown_lines.append(f"- {item}")
    else:
        markdown_lines.append("- None")

    markdown_lines.extend(["", "## Limits"])
    if limits:
        for item in limits:
            markdown_lines.append(f"- {item['kind']}: requested={item['requested']}, dropped={item['dropped']}")
    else:
        markdown_lines.append("- None")

    markdown_out = Path(args.markdown_out) if args.markdown_out else root / ".tmp-optimization-report.md"
    json_out = Path(args.json_out) if args.json_out else root / ".tmp-optimization-report.json"
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)

    markdown_out.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
