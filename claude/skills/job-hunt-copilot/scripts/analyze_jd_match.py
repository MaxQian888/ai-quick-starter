#!/usr/bin/env python3
"""把一份 JD 和用户的项目库做匹配分析，给出确定性的"挑哪些项目 + ATS 关键词覆盖"。

为什么存在这个脚本：旧版让模型每次手算"从项目库挑最匹配的项目""JD 关键词覆盖"，
既慢又不稳定，多次调用结果飘。把可量化的部分固化成脚本：项目相关度排序、JD 关键词
覆盖率、缺口关键词，都用确定算法算出来，模型只负责解读和给建议。

它不追求 NLP 级别的精度——目标是给模型一个可靠的起点，而不是替模型下结论。

用法:
    python analyze_jd_match.py --jd jd.txt --projects ../resources/projects [--json]
    python analyze_jd_match.py --jd-text "JD 原文…" --projects <dir>

输出（默认人类可读，--json 输出结构化）:
    - project_ranking : 每个项目对该 JD 的相关度得分 + 命中的能力标签，降序
    - covered         : JD 里出现、且项目库能讲到的关键词（应重点强调）
    - gaps            : JD 要求、但项目库里找不到的关键词（潜在 ATS 缺口）
    - match_score     : JD 关键词被项目库覆盖的比例

退出码: 0 成功; 2 入参/文件错误。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

# Windows 控制台默认 GBK，会让中文/emoji 输出乱码甚至抛 UnicodeEncodeError。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ── 停用词：英文常见词 + JD 套话，避免把"the""负责""要求"当成关键词 ──────────
EN_STOP = set(
    """a an the and or of to in on for with at by from as is are be been being this that these those
    you your we our they their it its will would can could should must may might have has had do does did
    not no all any both each more most other some such only own same so than too very just about into over
    under again further then once here there when where why how what which who whom whose if because while
    work working experience years year team teams role responsibilities requirements qualifications plus
    strong good excellent ability able including etc using use used across within per via able""".split()
)
CN_STOP = set(
    """的 了 和 与 及 或 在 是 我 你 他 她 它 们 这 那 有 为 对 等 把 被 让 等等 以及 并 且
    岗位 职责 要求 负责 工作 经验 能力 优先 熟悉 熟练 了解 掌握 具备 良好 相关 以上 至少 优秀
    我们 你们 公司 团队 加分 项 一 二 三 年 名 个 人""".split()
)
# 行内常见技术/软技能词，遇到时优先当关键词（提升中英混排 JD 的召回）
SOFT = {"沟通", "协作", "落地", "增长", "留存", "运营", "数据", "用户", "产品", "策略",
        "复盘", "迭代", "推动", "跨部门", "驱动", "洞察", "转化"}

EN_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-/]{1,}")
CJK = re.compile(r"[一-鿿]{2,}")


def extract_keywords(text: str) -> Counter:
    """从文本里抽候选关键词：英文 token + 中文 2~4 gram，附词频。"""
    kw: Counter = Counter()
    lower = text.lower()

    for tok in EN_TOKEN.findall(lower):
        if tok in EN_STOP or len(tok) < 2:
            continue
        kw[tok] += 1

    for run in CJK.findall(text):
        # 软技能词直接计入
        for s in SOFT:
            if s in run:
                kw[s] += 1
        # 2~4 gram 候选，过滤停用词
        for n in (4, 3, 2):
            for i in range(len(run) - n + 1):
                gram = run[i : i + n]
                if gram in CN_STOP or any(c in CN_STOP for c in gram):
                    continue
                kw[gram] += 1
    return kw


def _dedup_substrings(terms: list[str]) -> list[str]:
    """去掉被更长词包含的短词（如已有"用户留存"就删掉"留存"），降噪。"""
    terms_sorted = sorted(terms, key=len, reverse=True)
    kept: list[str] = []
    for t in terms_sorted:
        if any(t != k and t in k for k in kept):
            continue
        kept.append(t)
    return kept


def load_projects(projects_dir: str) -> list[dict]:
    projects = []
    for path in sorted(glob.glob(os.path.join(projects_dir, "*.md"))):
        name = os.path.splitext(os.path.basename(path))[0]
        if name.startswith("示例") or "可删除" in name:
            continue  # 跳过模板示例
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        tags = _extract_tags(content)
        projects.append({"name": name, "content": content, "tags": tags})
    return projects


def _extract_tags(content: str) -> list[str]:
    """抓"能力标签"小节里的 bullet 作为该项目的标签。"""
    m = re.search(r"##\s*能力标签(.*?)(?:\n##|\Z)", content, re.S)
    section = m.group(1) if m else content
    tags = re.findall(r"^[ \t]*[-*]\s*(.+?)\s*$", section, re.M)
    return [t.strip() for t in tags if t.strip()]


def analyze(jd_text: str, projects: list[dict]) -> dict:
    jd_kw = extract_keywords(jd_text)
    # 只保留较有信号的候选：词频>=2 或 是英文/软技能词
    candidates = [
        w for w, c in jd_kw.items()
        if c >= 2 or EN_TOKEN.fullmatch(w) or w in SOFT
    ]
    candidates = _dedup_substrings(candidates)
    # 按 JD 词频排序，取前 30 个，避免噪声淹没
    candidates.sort(key=lambda w: jd_kw[w], reverse=True)
    candidates = candidates[:30]

    library_text = "\n".join(p["content"] for p in projects).lower()
    all_tags = {t.lower() for p in projects for t in p["tags"]}

    covered, gaps = [], []
    for w in candidates:
        wl = w.lower()
        if wl in library_text or wl in all_tags:
            covered.append(w)
        else:
            gaps.append(w)

    match_score = round(100 * len(covered) / len(candidates)) if candidates else 0

    # 项目相关度：命中的 JD 关键词数（标签命中加权 2 倍）
    ranking = []
    jd_lower = jd_text.lower()
    for p in projects:
        content_l = p["content"].lower()
        tag_hits = [t for t in p["tags"] if t.lower() in jd_lower]
        kw_hits = [w for w in candidates if w.lower() in content_l]
        score = len(kw_hits) + len(tag_hits)  # 标签同时也在 kw_hits 里，自然加权
        ranking.append(
            {"project": p["name"], "score": score,
             "matched_tags": tag_hits, "matched_keywords": kw_hits}
        )
    ranking.sort(key=lambda r: r["score"], reverse=True)

    return {
        "match_score": match_score,
        "keywords_considered": candidates,
        "covered": covered,
        "gaps": gaps,
        "project_ranking": ranking,
    }


def render_human(result: dict) -> str:
    out = []
    out.append(f"## JD 匹配分析\n")
    out.append(f"**整体覆盖率**: {result['match_score']}%  "
               f"（JD 关键词 {len(result['keywords_considered'])} 个中，"
               f"项目库能讲到 {len(result['covered'])} 个）\n")

    out.append("### 项目相关度排序（建议优先选用前几个）")
    if not result["project_ranking"]:
        out.append("_项目库为空——请先用「项目录入」功能补充项目。_")
    for r in result["project_ranking"]:
        tags = "、".join(r["matched_tags"]) or "—"
        out.append(f"- **{r['project']}**（得分 {r['score']}）｜命中标签: {tags}")
    out.append("")

    out.append("### ✅ 已覆盖关键词（简历/讲稿应重点强调）")
    out.append("、".join(result["covered"]) if result["covered"] else "_无_")
    out.append("")

    out.append("### ⚠️ 缺口关键词（JD 要求但项目库找不到——考虑补素材或弱化）")
    out.append("、".join(result["gaps"]) if result["gaps"] else "_无明显缺口_")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="JD ↔ 项目库匹配 / ATS 关键词分析")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--jd", help="JD 文本文件路径")
    g.add_argument("--jd-text", help="直接传 JD 原文")
    ap.add_argument("--projects", required=True, help="项目库目录 (resources/projects)")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非人类可读文本")
    args = ap.parse_args()

    if args.jd:
        try:
            with open(args.jd, "r", encoding="utf-8") as fh:
                jd_text = fh.read()
        except OSError as exc:
            print(f"[analyze_jd] 读不到 JD 文件: {exc}", file=sys.stderr)
            return 2
    else:
        jd_text = args.jd_text

    if not jd_text.strip():
        print("[analyze_jd] JD 内容为空。", file=sys.stderr)
        return 2
    if not os.path.isdir(args.projects):
        print(f"[analyze_jd] 项目库目录不存在: {args.projects}", file=sys.stderr)
        return 2

    projects = load_projects(args.projects)
    result = analyze(jd_text, projects)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
