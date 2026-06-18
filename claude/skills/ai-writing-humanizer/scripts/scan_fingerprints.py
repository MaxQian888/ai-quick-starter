#!/usr/bin/env python3
"""
AI 写作硬指纹扫描器（纯字符串扫描，无外部依赖）。

用法:
    python scan_fingerprints.py --text "<文本>" [--lang zh|en|auto]
    python scan_fingerprints.py --file <path> [--lang zh|en|auto]
    echo "<文本>" | python scan_fingerprints.py --stdin --lang zh

输出: 单个 JSON 对象到 stdout, 包含 stats / hits / structural_warnings。
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

# 中文硬指纹词表（命中即报）
ZH_PATTERNS = {
    "过渡套话": [
        "综上所述", "总而言之", "综合来看", "综合分析", "综合而言",
        "此外", "另外值得一提", "值得注意的是", "值得一提的是",
        "不可否认", "众所周知", "毋庸置疑",
        "首先", "其次", "再次", "最后",
        "在这个", "在当今", "在这样一个",
    ],
    "关联结构套话": [
        "不仅", "而且也", "既...又", "一方面", "另一方面",
        "无论...都", "在...的同时", "相辅相成", "与此同时",
    ],
    "夸大空话": [
        "广受好评", "深受喜爱", "深受欢迎", "引发广泛关注",
        "具有重要意义", "产生深远影响", "备受瞩目",
        "业内人士表示", "专家指出",
    ],
    "空话收尾": [
        "挑战与机遇并存", "未来可期", "拭目以待",
        "让我们一起", "让我们携手", "迈向新阶段", "开启新篇章",
        "画上句号", "再上新台阶", "勇立潮头",
        "赋能千行百业", "迎接更美好的未来",
    ],
    "奉承尾巴": [
        "希望以上内容对您有所帮助", "希望对您有所启发",
        "如有任何问题，欢迎随时告诉我", "如有问题请告诉我",
        "感谢您的阅读", "祝您工作顺利", "祝您学习愉快",
        "截至我所了解的信息", "根据我现有的知识",
    ],
    "弱化动词词组": [
        "做出了一个决定", "做出决定", "进行了讨论", "进行讨论",
        "加以解决", "进行优化", "做出贡献", "起到推动作用",
        "实现...的目标", "给予帮助",
    ],
    "限定词膨胀": [
        # 单独命中不算重，连续命中或高频才算
        "非常", "其实", "基本上", "实际上", "大概",
        "相对而言", "总体而言", "应该说", "可以说",
        "在某种程度上", "确实", "的确",
    ],
}

EN_PATTERNS = {
    "Overused verbs (Tier 1)": [
        r"\bdelve\b", r"\bembark\b", r"\bharness\b", r"\bleverage\b",
        r"\butilize\b", r"\bfoster\b", r"\bunderscore\b",
        r"\billuminate\b", r"\bunveil\b", r"\belucidate\b",
        r"\bnavigate\b", r"\bstreamline\b", r"\bamplify\b",
        r"\bbolster\b", r"\btranscend\b", r"\bspearhead\b",
        r"\bcatalyze\b", r"\brevolutionize\b",
    ],
    "Overused adjectives": [
        r"\bpivotal\b", r"\brobust\b", r"\bseamless\b", r"\bintricate\b",
        r"\bcutting[- ]edge\b", r"\bgroundbreaking\b", r"\bbespoke\b",
        r"\bparamount\b", r"\bprofound\b", r"\bmeticulous\b",
        r"\bunparalleled\b", r"\bunprecedented\b", r"\bcomprehensive\b",
    ],
    "Overused nouns": [
        r"\btapestry\b", r"\brealm\b", r"\blandscape\b", r"\bbeacon\b",
        r"\btestament\b", r"\btreasure trove\b", r"\bsynergy\b",
        r"\binterplay\b", r"\bcacophony\b", r"\bsymphony\b",
        r"\bparadigm\b", r"\becosystem\b",
    ],
    "Transition fillers": [
        r"\bFurthermore\b", r"\bMoreover\b", r"\bIn addition\b",
        r"\bIt is worth noting\b", r"\bIt's important to note\b",
        r"\bIn conclusion\b", r"\bIn summary\b", r"\bTo sum up\b",
        r"\bAll things considered\b", r"\bAt the end of the day\b",
    ],
    "Setup language": [
        r"\bIn a world where\b", r"\bIn today's fast[- ]paced\b",
        r"\bWhen it comes to\b", r"\bHave you ever wondered\b",
        r"\bDid you know\b", r"\bImagine a\b",
    ],
    "Negative parallelism": [
        r"\bnot just\b.*\bbut\b", r"\bisn't just\b.*\bit'?s\b",
        r"\bnot only\b.*\bbut also\b",
    ],
    "Sycophantic closers": [
        r"I hope this helps!?", r"Let me know if you have any questions",
        r"Feel free to ask", r"Thanks for reading!?",
        r"Hope you found this useful",
    ],
}


def detect_lang(text: str) -> str:
    """检测语种: 中文字符占比 > 30% → zh, 否则 en."""
    if not text:
        return "en"
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    return "zh" if cjk / len(text) > 0.30 else "en"


def split_sentences(text: str, lang: str):
    """按句号 / 问号 / 感叹号 / 中文句号切句."""
    if lang == "zh":
        parts = re.split(r"[。！？；\n]+", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in parts if s.strip()]


def sentence_length(s: str, lang: str) -> int:
    """中文用字符数, 英文用 word 数."""
    if lang == "zh":
        return sum(1 for ch in s if not ch.isspace())
    return len(re.findall(r"\b\w+\b", s))


def scan_zh(text: str):
    hits = []
    for category, terms in ZH_PATTERNS.items():
        for term in terms:
            for m in re.finditer(re.escape(term), text):
                start = m.start()
                line = text[:start].count("\n") + 1
                ctx_start = max(0, start - 15)
                ctx_end = min(len(text), m.end() + 15)
                context = text[ctx_start:ctx_end].replace("\n", " ")
                hits.append({
                    "category": category,
                    "term": term,
                    "line": line,
                    "offset": start,
                    "context": context,
                })
    return hits


def scan_en(text: str):
    hits = []
    for category, patterns in EN_PATTERNS.items():
        for pat in patterns:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                start = m.start()
                line = text[:start].count("\n") + 1
                ctx_start = max(0, start - 20)
                ctx_end = min(len(text), m.end() + 20)
                context = text[ctx_start:ctx_end].replace("\n", " ")
                hits.append({
                    "category": category,
                    "term": m.group(0),
                    "line": line,
                    "offset": start,
                    "context": context,
                })
    return hits


def scan_em_dash(text: str, total_units: int):
    """em-dash 频率: 中文 ≤ 1 / 200 字, 英文 ≤ 1 / 200 词."""
    # 包括 — (U+2014), – (U+2013), 和 -- (双连字符)
    em_count = text.count("—") + text.count("–") + len(re.findall(r"--", text))
    if total_units == 0:
        return None
    rate = em_count / total_units * 200
    if em_count > 0:
        return {
            "category": "em-dash 频率",
            "count": em_count,
            "per_200_units": round(rate, 2),
            "threshold": "≤ 1 / 200 字或词",
            "hit": rate > 1.0,
        }
    return None


def scan_structure(text: str, lang: str):
    """结构层警告: 句长方差 / 段首多样性 / 三联词."""
    warnings = []
    sentences = split_sentences(text, lang)
    if len(sentences) >= 3:
        lengths = [sentence_length(s, lang) for s in sentences]
        try:
            sd = statistics.stdev(lengths)
            warnings.append({
                "metric": "句长标准差",
                "value": round(sd, 2),
                "recommended_min": 4,
                "hit": sd < 4,
            })
        except statistics.StatisticsError:
            pass

        # 连续 3 句长度差距小
        for i in range(len(lengths) - 2):
            window = lengths[i:i+3]
            if max(window) - min(window) < 5:
                warnings.append({
                    "metric": "连续 3 句长度相近",
                    "position": f"句 {i+1}-{i+3}",
                    "lengths": window,
                })
                break  # 只报一次

    # 段首多样性 (按段落, 多段时检查)
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) >= 3:
        # 段首词重复率
        first_chars = []
        for p in paragraphs:
            first_sent = split_sentences(p, lang)
            if first_sent:
                first_chars.append(first_sent[0][:4] if lang == "zh"
                                   else first_sent[0].split()[0] if first_sent[0].split() else "")
        # 重复率
        if first_chars:
            unique_ratio = len(set(first_chars)) / len(first_chars)
            if unique_ratio < 0.5:
                warnings.append({
                    "metric": "段首多样性",
                    "unique_ratio": round(unique_ratio, 2),
                    "note": "段落开头重复严重",
                })

    # 三联词模式 (中英文)
    if lang == "zh":
        triads = re.findall(r"[一-鿿]{1,3}、[一-鿿]{1,3}、[一-鿿]{1,3}", text)
        if len(triads) >= 1:
            warnings.append({
                "metric": "中文三联词",
                "examples": triads[:3],
                "count": len(triads),
            })
    else:
        triads = re.findall(r"\b\w+,\s+\w+,\s+and\s+\w+\b", text, flags=re.IGNORECASE)
        if len(triads) >= 1:
            warnings.append({
                "metric": "English triadic structures",
                "examples": triads[:3],
                "count": len(triads),
            })

    return warnings


def scan_semantic(text: str, lang: str):
    """语义层警告: 具体名词缺失 / 第一人称缺失 / 数字缺失."""
    warnings = []
    if lang == "zh":
        # 数字检测
        digits = re.findall(r"\d+", text)
        if len(digits) == 0:
            warnings.append({"metric": "零数字", "note": "全文没有任何数字 / 比例"})
        # 第一人称
        first_person = re.findall(r"[我咱]", text)
        if len(first_person) == 0:
            warnings.append({"metric": "零第一人称", "note": "通篇无 '我 / 咱'"})
    else:
        digits = re.findall(r"\d+", text)
        if len(digits) == 0:
            warnings.append({"metric": "no digits", "note": "no numbers in text"})
        first_person = re.findall(r"\b(I|we|me|my|our|us)\b", text)
        if len(first_person) == 0:
            warnings.append({"metric": "no first person", "note": "no I/we/me anywhere"})
    return warnings


def main():
    ap = argparse.ArgumentParser(description="AI 写作硬指纹扫描器")
    ap.add_argument("--text", type=str, help="直接传入文本")
    ap.add_argument("--file", type=str, help="读取文件路径")
    ap.add_argument("--stdin", action="store_true", help="从 stdin 读取")
    ap.add_argument("--lang", choices=["zh", "en", "auto"], default="auto")
    args = ap.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        print(json.dumps({"error": "No input provided. Use --text / --file / --stdin"}, ensure_ascii=False))
        sys.exit(1)

    lang = args.lang
    if lang == "auto":
        lang = detect_lang(text)

    sentences = split_sentences(text, lang)
    lengths = [sentence_length(s, lang) for s in sentences]
    total_units = (sum(1 for ch in text if not ch.isspace())
                   if lang == "zh"
                   else len(re.findall(r"\b\w+\b", text)))

    stats = {
        "lang": lang,
        "total_chars" if lang == "zh" else "total_words": total_units,
        "sentences": len(sentences),
        "sentence_length_mean": round(statistics.mean(lengths), 2) if lengths else 0,
        "sentence_length_stddev": round(statistics.stdev(lengths), 2) if len(lengths) >= 2 else 0,
    }

    hits = scan_zh(text) if lang == "zh" else scan_en(text)
    em_hit = scan_em_dash(text, total_units)
    if em_hit:
        hits.append(em_hit)

    structural_warnings = scan_structure(text, lang)
    semantic_warnings = scan_semantic(text, lang)

    # 总评
    hard_hits = len([h for h in hits if h.get("category") not in ["限定词膨胀"]])
    if hard_hits >= 5:
        verdict = "高 AI 浓度"
    elif hard_hits >= 2:
        verdict = "中 AI 浓度"
    else:
        verdict = "低 AI 浓度"

    result = {
        "stats": stats,
        "verdict": verdict,
        "hits": hits,
        "structural_warnings": structural_warnings,
        "semantic_warnings": semantic_warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
