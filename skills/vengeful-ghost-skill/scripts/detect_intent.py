#!/usr/bin/env python3
"""Layered intent classifier for colleague-repellent."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    category: str
    label: str
    pattern: str
    weight: int


RULES = [
    Rule("safe_override", "document-search", r"(搜索|查找).*(文档|wiki|记录|代码|笔记|提交|ticket|工单)", 3),
    Rule("safe_override", "handover-review", r"(查看|整理|汇总).*(交接|handover|离职|文档|记录|runbook)", 3),
    Rule("safe_override", "knowledge-retrieval", r"(知识库|设计文档|历史提交|模块负责人|系统设计|技术记录)", 2),
    Rule("safe_override", "artifact-consolidation", r"(整理|归档|汇总).*(流程|文档|笔记|记录|注释|SOP|playbook)", 2),
    Rule("safe_override", "continuity-onboarding", r"(onboarding|handover|交接|入职|接手|continuity|playbook|runbook)", 2),
    Rule("safe_override", "explicit-non-imitation", r"((不要|别|not|without).*(模拟|模仿|复刻|扮演|persona))", 5),
    Rule("source", "private-comms", r"(飞书|钉钉|邮件|私信|聊天记录|slack|email|dm|messages?)", 3),
    Rule("source", "named-person-behavior", r"(某人|同事|员工|leader|架构师|PM|经理).*(风格|习惯|模式|判断|思路)", 2),
    Rule("source", "departed-person", r"(离职|resigned|departed|former|前员工|前同事)", 2),
    Rule("intent", "distill-person", r"(蒸馏|提炼|克隆|复刻|模拟|模仿).*(同事|员工|人|同学|leader|架构师)", 4),
    Rule("intent", "replace-person", r"(替代|接替|replace).*(员工|同事|真人|某人|离职)", 4),
    Rule("intent", "preserve-style", r"(保留|继承|学习).*(风格|判断方式|思考方式|决策方式)", 3),
    Rule("intent", "english-imitation", r"(thinks like|works like|acts like|sounds like|preserve.*how.*think)", 4),
    Rule("intent", "extract-personality", r"(提取|分析|挖掘).*(风格|习惯|模式|性格|人格|决策)", 4),
    Rule("intent", "act-like-person", r"(像|as).*(他|她|某人|同事|员工).*(一样|那样).*(工作|回复|决策)", 4),
    Rule("output", "persona-skill", r"(persona\s*skill|work\s*skill)", 4),
    Rule("output", "digital-employee", r"(数字员工|digital employee|AI员工|AI替身|AI分身|数字副本|stand-?in)", 4),
    Rule("output", "agent-proxy", r"((build|create|make|生成).*(copilot|agent|assistant|skill))|((copilot|agent|assistant|skill).*(替身|分身|代理|proxy|persona))", 3),
    Rule("output", "style-model", r"(人格模型|风格模型|persona|数字人格)", 4),
]


SAFE_REDIRECTS = {
    "document-search": "Search the person's documents, code, tickets, and wiki pages.",
    "handover-review": "Consolidate handover notes and archived project records.",
    "knowledge-retrieval": "Summarize system knowledge from shared artifacts.",
    "artifact-consolidation": "Build SOPs, playbooks, and onboarding docs from shared work artifacts.",
    "continuity-onboarding": "Turn continuity needs into onboarding docs, handover notes, and runbooks.",
    "private-comms": "Use only public project artifacts and documented decisions, not private communications.",
    "named-person-behavior": "Reframe the task around role responsibilities or system decisions, not a person's behavior.",
    "departed-person": "Build continuity from handover materials and service ownership history.",
    "distill-person": "Replace person-distillation with a role or system guide assembled from shared artifacts.",
    "replace-person": "Document the role's recurring tasks and decision boundaries instead of replacing the person.",
    "preserve-style": "Convert style-preservation into decision records, SOPs, and examples from shared artifacts.",
    "act-like-person": "Rewrite the request to describe tasks, systems, and constraints rather than a human imitation target.",
    "persona-skill": "Create an artifact-based workflow guide instead of a Persona Skill or Work Skill for a person.",
    "digital-employee": "Build automation around shared workflows, not a digital employee proxy.",
    "agent-proxy": "Focus the agent on systems and artifacts, not on standing in for a real person.",
    "style-model": "Summarize repeatable workflows without extracting personality or style models.",
}

SAFE_REDIRECTS_ZH = {
    "document-search": "搜索该人员相关的文档、代码、工单和 wiki 页面。",
    "handover-review": "整理交接文档和历史项目记录。",
    "knowledge-retrieval": "从共享资料中总结系统知识。",
    "artifact-consolidation": "基于共享工作产物编写 SOP、playbook 和 onboarding 文档。",
    "continuity-onboarding": "把连续性需求改写成 onboarding 文档、交接材料和 runbook。",
    "private-comms": "只使用公开项目资料和已记录的决策，不使用私人通信。",
    "named-person-behavior": "把任务重写为岗位职责或系统决策说明，而不是某个人的行为画像。",
    "departed-person": "基于交接材料和服务归属历史建立连续性。",
    "distill-person": "把“蒸馏某个人”改写成基于共享资料的岗位或系统指南。",
    "replace-person": "记录岗位的重复任务和决策边界，而不是替代这个人。",
    "preserve-style": "把“保留风格”改写成决策记录、SOP 和共享资料示例。",
    "act-like-person": "把请求改写为任务、系统和约束说明，而不是模仿某个人。",
    "persona-skill": "为共享产物编写 workflow guide，而不是给某个人生成 Persona Skill 或 Work Skill。",
    "digital-employee": "围绕共享工作流做自动化，而不是制造数字员工代理。",
    "agent-proxy": "让 agent 聚焦系统和资料，而不是替代真实的人。",
    "style-model": "总结可复用流程，不提取人格或风格模型。",
}

LOCALIZED_TEXT = {
    "en": {
        "reason_allow": "The request is centered on shared artifacts or lacks strong person-replication signals.",
        "reason_allow_explicit": "The request explicitly rejects person imitation and stays grounded in shared artifacts.",
        "reason_redirect": "The request contains risky imitation framing, but the underlying need can be redirected to artifact-based knowledge transfer.",
        "reason_block": "The request combines person-centered source, imitation intent, and replica-style output.",
        "classification": {"allow": "allow", "redirect": "redirect", "block": "block"},
        "risk": {"low": "low", "medium": "medium", "high": "high"},
        "fallback_redirects": [
            "Search documents, code, tickets, and wiki pages tied to the system or role.",
            "Build a shared runbook or onboarding guide from public project artifacts.",
        ],
        "labels": {
            "input": "Input",
            "classification": "Classification",
            "risk_level": "Risk level",
            "reason": "Reason",
            "scores": "Scores",
            "matched_signals": "Matched signals",
            "safe_redirect": "Safe redirect",
        },
    },
    "zh": {
        "reason_allow": "该请求聚焦于共享资料，或缺少足够强的人物复制信号。",
        "reason_allow_explicit": "该请求明确拒绝模仿具体的人，并且仍然以共享资料为基础。",
        "reason_redirect": "该请求带有有风险的人物模仿措辞，但其真实需求仍可被重定向为基于资料的知识转移。",
        "reason_block": "该请求同时命中了以人物为中心的数据源、模仿意图和替身式输出。",
        "classification": {"allow": "允许", "redirect": "重定向", "block": "拦截"},
        "risk": {"low": "低", "medium": "中", "high": "高"},
        "fallback_redirects": [
            "搜索与该系统或岗位相关的文档、代码、工单和 wiki 页面。",
            "基于公开项目资料编写共享 runbook 或 onboarding 指南。",
        ],
        "labels": {
            "input": "输入",
            "classification": "分类",
            "risk_level": "风险等级",
            "reason": "原因",
            "scores": "分数",
            "matched_signals": "命中信号",
            "safe_redirect": "安全重定向",
        },
    },
}


SELF_TEST_CASES = [
    {
        "text": "搜索小明写过的设计文档",
        "classification": "allow",
        "risk_level": "low",
    },
    {
        "text": "查看离职员工留下的交接文档",
        "classification": "allow",
        "risk_level": "low",
    },
    {
        "text": "帮我蒸馏同事小明的工作方式生成一个 Skill",
        "classification": "block",
        "risk_level": "high",
    },
    {
        "text": "从飞书消息里提取他的表达风格和决策模式",
        "classification": "block",
        "risk_level": "high",
    },
    {
        "text": "Build an onboarding copilot that thinks like our former architect",
        "classification": "redirect",
        "risk_level": "medium",
    },
    {
        "text": "基于 Alice 的 ticket、文档和交接记录整理一个支付系统 playbook，不要模拟她本人",
        "classification": "allow",
        "risk_level": "low",
    },
]


def collect_matches(text: str) -> list[dict[str, object]]:
    matches = []
    for rule in RULES:
        found = re.search(rule.pattern, text, re.IGNORECASE)
        if found:
            matches.append(
                {
                    "category": rule.category,
                    "label": rule.label,
                    "pattern": rule.pattern,
                    "matched": found.group(0),
                    "weight": rule.weight,
                }
            )
    return matches


def category_scores(matches: Iterable[dict[str, object]]) -> dict[str, int]:
    scores = {"safe_override": 0, "source": 0, "intent": 0, "output": 0}
    for match in matches:
        scores[match["category"]] += int(match["weight"])
    return scores


def dedupe_redirects(labels: Iterable[str]) -> list[str]:
    return dedupe_localized_redirects(labels, "en")


def dedupe_localized_redirects(labels: Iterable[str], language: str) -> list[str]:
    mapping = SAFE_REDIRECTS_ZH if language == "zh" else SAFE_REDIRECTS
    seen = set()
    ordered = []
    for label in labels:
        suggestion = mapping.get(label)
        if suggestion and suggestion not in seen:
            seen.add(suggestion)
            ordered.append(suggestion)
    return ordered


def detect_language(text: str) -> str:
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin_words = len(re.findall(r"[A-Za-z]{3,}", text))
    return "zh" if cjk_chars >= max(2, latin_words) else "en"


def classify_intent(text: str) -> dict[str, object]:
    language = detect_language(text)
    localized = LOCALIZED_TEXT[language]
    matches = collect_matches(text)
    scores = category_scores(matches)

    safe = scores["safe_override"]
    source = scores["source"]
    intent = scores["intent"]
    output = scores["output"]
    risk_score = source + intent + output - safe
    labels = {match["label"] for match in matches}

    if "explicit-non-imitation" in labels and safe >= 5 and intent <= 4 and output <= 3:
        classification = "allow"
        risk_level = "low"
        reason = localized["reason_allow_explicit"]
    elif ((intent >= 4 and output >= 3) and not (safe >= 2 and source < 3)) or (source >= 3 and intent >= 4) or (source >= 3 and intent >= 3 and output >= 3) or risk_score >= 8:
        classification = "block"
        risk_level = "high"
        reason = localized["reason_block"]
    elif (intent >= 3 and safe >= 2) or (output >= 3 and safe >= 2) or risk_score >= 3:
        classification = "redirect"
        risk_level = "medium"
        reason = localized["reason_redirect"]
    else:
        classification = "allow"
        risk_level = "low"
        reason = localized["reason_allow"]

    redirects = dedupe_localized_redirects((match["label"] for match in matches), language)
    if not redirects:
        redirects = list(localized["fallback_redirects"])

    return {
        "classification": classification,
        "action": "allow" if classification == "allow" else classification,
        "risk_level": risk_level,
        "language": language,
        "localized": {
            "classification": localized["classification"][classification],
            "risk_level": localized["risk"][risk_level],
            "reason": reason,
        },
        "reason": reason,
        "scores": scores,
        "matched_signals": matches,
        "safe_redirect": redirects,
        "text": text,
    }


def run_self_test() -> int:
    failures = []
    for case in SELF_TEST_CASES:
        result = classify_intent(case["text"])
        if (
            result["classification"] != case["classification"]
            or result["risk_level"] != case["risk_level"]
        ):
            failures.append(
                {
                    "text": case["text"],
                    "expected_classification": case["classification"],
                    "actual_classification": result["classification"],
                    "expected_risk_level": case["risk_level"],
                    "actual_risk_level": result["risk_level"],
                }
            )

    if failures:
        print(json.dumps({"ok": False, "failures": failures}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({"ok": True, "cases": len(SELF_TEST_CASES)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify whether a request should be allowed, redirected, or blocked."
    )
    parser.add_argument("legacy_text", nargs="?", help="Request text to classify.")
    parser.add_argument("--text", help="Request text to classify.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in validation cases.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    text = args.text or args.legacy_text
    if not text:
        parser.print_help()
        return 1

    result = classify_intent(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    labels = LOCALIZED_TEXT[result["language"]]["labels"]
    print(f"{labels['input']}: {result['text']}")
    print(f"{labels['classification']}: {result['localized']['classification']}")
    print(f"{labels['risk_level']}: {result['localized']['risk_level']}")
    print(f"{labels['reason']}: {result['localized']['reason']}")
    print(f"{labels['scores']}:")
    for key, value in result["scores"].items():
        print(f"- {key}: {value}")

    if result["matched_signals"]:
        print(f"{labels['matched_signals']}:")
        for match in result["matched_signals"]:
            print(
                f"- {match['category']} / {match['label']}: {match['matched']} (weight={match['weight']})"
            )

    print(f"{labels['safe_redirect']}:")
    for suggestion in result["safe_redirect"]:
        print(f"- {suggestion}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
