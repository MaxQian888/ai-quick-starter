#!/usr/bin/env python3
"""Route academic writing requests to the best local workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCES = [
    "references/usage-map.md",
    "references/components-and-setup.md",
    "references/cache/upstream-section-index.json",
]

COMPONENT_ALIASES = {
    "openskills": "openskills",
    "open skills": "openskills",
    "20-ml-paper-writing": "20-ml-paper-writing",
    "ml-paper-writing": "20-ml-paper-writing",
    "humanizer": "humanizer",
    "docx": "docx",
    "doc-coauthoring": "doc-coauthoring",
    "canvas-design": "canvas-design",
}

ROUTES = [
    {
        "workflow_id": "skills-setup",
        "category": "installation",
        "matched_sections": ["Skills 的配置", "Skills 总览", "使用场景与示例 Prompt"],
        "keywords": [
            "安装",
            "配置",
            "setup",
            "install",
            "openskills",
            "组件",
            "component",
            "skill",
            "skills",
        ],
        "related_components": ["openskills", "20-ml-paper-writing", "humanizer", "docx", "doc-coauthoring", "canvas-design"],
        "next_steps": [
            "Run scripts/install_components.py to build an installation plan.",
            "Use the local component map before invoking interactive OpenSkills installers.",
        ],
    },
    {
        "workflow_id": "reviewer-audit",
        "category": "prompt",
        "matched_sections": ["论文整体以 Reviewer 视角进行审视"],
        "keywords": ["reviewer", "审稿报告", "拒稿", "致命问题", "weakness", "rating", "strategic advice"],
        "related_components": ["20-ml-paper-writing"],
        "next_steps": [
            "Load the reviewer section from the upstream cache.",
            "If the user supplied a PDF or full draft, keep the response in review-report format.",
        ],
    },
    {
        "workflow_id": "cn-to-en",
        "category": "prompt",
        "matched_sections": ["中转英"],
        "keywords": ["中转英", "中文", "翻译成英文", "英文学术", "latex", "translate to english"],
        "related_components": [],
        "next_steps": [
            "Use the upstream 中转英 prompt with the user's Chinese draft.",
            "Preserve math and LaTeX commands while translating.",
        ],
    },
    {
        "workflow_id": "en-to-cn",
        "category": "prompt",
        "matched_sections": ["英转中"],
        "keywords": ["英转中", "翻译成中文", "latex english", "translate to chinese"],
        "related_components": [],
        "next_steps": [
            "Use the upstream 英转中 prompt.",
            "Strip disruptive LaTeX references while keeping meaning aligned to the source.",
        ],
    },
    {
        "workflow_id": "zh-refine",
        "category": "prompt",
        "matched_sections": ["中转中", "表达润色（中文论文）", "去 AI 味（Word 中文）"],
        "keywords": ["中转中", "中文润色", "word 中文", "去ai味", "去 ai 味", "humanize chinese", "中文论文"],
        "related_components": ["humanizer"],
        "next_steps": [
            "Choose the most conservative Chinese prompt that fits the request.",
            "Keep Word-friendly output when the user mentions Word or plain-text copy/paste.",
        ],
    },
    {
        "workflow_id": "en-refine",
        "category": "prompt",
        "matched_sections": ["表达润色（英文论文）", "去 AI 味（LaTeX 英文）", "缩写", "扩写", "逻辑检查"],
        "keywords": ["英文润色", "latex 英文", "humanize", "缩写", "扩写", "逻辑检查", "polish english"],
        "related_components": ["humanizer"],
        "next_steps": [
            "Pick the narrowest English-writing prompt that matches the ask.",
            "Default to LaTeX-preserving output when the request includes equations or .tex content.",
        ],
    },
    {
        "workflow_id": "visual-support",
        "category": "prompt",
        "matched_sections": ["论文架构图", "实验绘图推荐", "生成图的标题", "生成表的标题", "实验分析"],
        "keywords": ["架构图", "绘图", "caption", "标题", "图标题", "表标题", "实验分析", "visual", "figure", "table"],
        "related_components": ["canvas-design", "20-ml-paper-writing"],
        "next_steps": [
            "Use the prompt family that matches figure design, chart recommendation, captioning, or experiment analysis.",
            "Recommend canvas-design when the user needs a fresh diagram, not just wording.",
        ],
    },
]


def normalize_text(text: str) -> str:
    return " ".join(text.lower().replace("/", " ").replace("_", " ").split())


def extract_requested_components(request: str) -> list[str]:
    normalized = normalize_text(request)
    matches: list[str] = []
    for alias, component in COMPONENT_ALIASES.items():
        if alias in normalized and component not in matches:
            matches.append(component)
    return matches


def select_workflow(request: str) -> dict[str, object]:
    normalized = normalize_text(request)
    requested_components = extract_requested_components(request)

    for route in ROUTES:
        if any(keyword in normalized for keyword in route["keywords"]):
            related_components = list(route["related_components"])
            for component in requested_components:
                if component not in related_components:
                    related_components.append(component)
            return {
                "workflow_id": route["workflow_id"],
                "category": route["category"],
                "matched_sections": route["matched_sections"],
                "related_components": related_components,
                "references": list(DEFAULT_REFERENCES),
                "reason": f"Matched keywords for {route['workflow_id']}.",
                "next_steps": route["next_steps"],
            }

    fallback_sections = ["Part I: 写作 Prompt 集合", "Part II: 论文写作相关的 Agent-Skills"]
    return {
        "workflow_id": "general-academic-writing",
        "category": "prompt",
        "matched_sections": fallback_sections,
        "related_components": requested_components,
        "references": list(DEFAULT_REFERENCES),
        "reason": "No narrow workflow matched, so the skill should start from the broad academic writing map.",
        "next_steps": [
            "Open references/usage-map.md and choose the narrowest applicable section.",
            "Refresh the upstream cache if the section index is missing or stale.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route a paper-writing request to the best ai-research-writing workflow.")
    parser.add_argument("request", nargs="?", default="", help="User request to classify. Reads stdin when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    request = args.request or sys.stdin.read().strip()
    if not request:
        print("A request is required.", file=sys.stderr)
        return 1

    result = select_workflow(request)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"workflow_id={result['workflow_id']}")
    print(f"category={result['category']}")
    print("matched_sections=" + " | ".join(result["matched_sections"]))
    print("related_components=" + ", ".join(result["related_components"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
