#!/usr/bin/env python3
"""
QQ群成员批量画像构建器

负责从群聊导出中筛选候选成员，生成 dry-run 摘要，并按策略批量创建或更新群友 skill。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import qq_chat_parser  # type: ignore  # noqa: E402
import skill_writer  # type: ignore  # noqa: E402


DEFAULT_MIN_MESSAGES = 20
DEFAULT_MODE = "dry-run"
DEFAULT_ON_EXISTS = "skip"
BRACKET_TOKEN_PATTERN = re.compile(r"^(?:\[[^\]]+\])+$")
MEANINGFUL_CHAR_PATTERN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]")


TAG_RULES = {
    "话痨": "在群聊中发言频率高，接话快，容易把短对话聊成连续多条消息。",
    "话少": "更偏向短句发言，只有话题碰到点上时才会多说几句。",
    "爱发表情包": "遇到好笑或需要接梗的时候，会优先用表情包或图片代替长篇解释。",
    "爱发语音": "当一句话说不清时，会倾向于改用更直接的表达方式而不是慢慢打字。",
    "秒回": "对群聊动态反应快，被点到时通常会第一时间出现。",
    "潜水党": "平时存在感不高，但熟悉的话题会突然冒出来接一句。",
    "刷屏党": "同一轮话题里容易连发多条，把气氛往前推。",
    "开朗": "整体语气外放，不太端着，愿意主动把群里的气氛带起来。",
    "内向": "说话更收着，通常先观察气氛，再挑自己确定的话题接话。",
    "幽默": "喜欢顺手接梗、玩笑化表达，聊天时会刻意留一点轻松感。",
    "严肃": "更在意把信息说清楚，不会为了热闹牺牲表达准确性。",
    "急性子": "表达节奏快，想到什么就会直接抛出来，不爱铺垫。",
    "慢性子": "回话节奏偏稳，不会被群里节奏推着走。",
    "直率": "表达结论比较直接，不太绕弯子。",
    "含蓄": "碰到敏感或拿不准的话题，会用更委婉的说法留余地。",
    "热情": "对熟人和熟话题投入度高，会主动把话题接下去。",
    "冷漠": "除非必要，不会刻意扩展聊天，表达以够用为主。",
    "直接": "更偏结论先行，习惯先给态度再补理由。",
    "绕弯子": "会先铺垫气氛，再慢慢把真正想说的内容带出来。",
    "毒舌": "开玩笑时会带一点刺，但重点仍在逗乐而不是恶意攻击。",
    "温柔": "即使不同意，也会尽量把话说得不让人难堪。",
    "理性": "讨论问题时会优先看逻辑和结论，不容易被情绪直接带跑。",
    "感性": "表达里会更明显地带出情绪和个人感受。",
    "爱抬杠": "遇到观点不对劲时会忍不住抬一句，喜欢把细节掰清楚。",
    "爱附和": "更倾向于顺着群里的主节奏回应，减少正面冲突。",
}


def ensure_utf8_stdio() -> None:
    """在 Windows 控制台下尽量避免输出 emoji 时的编码报错。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def load_mapping(mapping_path: str | None) -> dict:
    """读取批量映射配置。"""
    if not mapping_path:
        return {}

    path = Path(mapping_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到映射文件：{path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("映射文件必须是 JSON 对象")
    return data


def resolve_min_messages(cli_value: int | None, mapping: dict | None) -> int:
    """解析最终的最小发言数阈值。"""
    if cli_value is not None:
        return cli_value

    defaults = (mapping or {}).get("defaults", {})
    if isinstance(defaults, dict):
        mapped = defaults.get("min_messages")
        if isinstance(mapped, int):
            return mapped

    return DEFAULT_MIN_MESSAGES


def load_messages(file_path: str) -> list[dict]:
    """按后缀选择群聊解析方式。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到聊天记录文件：{path}")

    if path.suffix.lower() == ".json":
        return qq_chat_parser.parse_qq_json(str(path), "")
    return qq_chat_parser.parse_qq_txt(str(path), "")


def merge_identifier_filters(
    mapping: dict | None,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> tuple[set[str], set[str]]:
    """合并 CLI 与映射文件里的 include/exclude。"""
    include_set = {str(item) for item in include or [] if str(item).strip()}
    exclude_set = {str(item) for item in exclude or [] if str(item).strip()}

    if isinstance(mapping, dict):
        include_set.update(str(item) for item in mapping.get("include", []) if str(item).strip())
        exclude_set.update(str(item) for item in mapping.get("exclude", []) if str(item).strip())

    return include_set, exclude_set


def resolve_alias(mapping: dict | None, sender_key: str, source_name: str) -> dict:
    """按 sender_id 或原始显示名查找别名配置。"""
    aliases = (mapping or {}).get("aliases", {})
    if not isinstance(aliases, dict):
        return {}

    value = aliases.get(sender_key)
    if isinstance(value, dict):
        return value

    value = aliases.get(source_name)
    if isinstance(value, dict):
        return value

    return {}


def _clean_preview_text(content: str) -> str:
    text = (content or "").strip()
    if not text:
        return ""

    if "\n" in text:
        parts = [part.strip() for part in text.splitlines() if part.strip()]
        if parts:
            text = parts[-1]

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_low_signal_phrase(text: str) -> bool:
    """过滤预览中信息量过低的短句。"""
    normalized = (text or "").strip()
    if not normalized:
        return True
    if BRACKET_TOKEN_PATTERN.match(normalized):
        return True
    if not MEANINGFUL_CHAR_PATTERN.search(normalized):
        return True
    return False


def extract_top_phrases(messages: list[dict], limit: int = 3) -> list[str]:
    """提取批量预览里最有辨识度的高频短句。"""
    counter: Counter[str] = Counter()

    for msg in messages:
        text = _clean_preview_text(str(msg.get("content", "")))
        if not text or len(text) > 20:
            continue
        if is_low_signal_phrase(text):
            continue
        counter[text] += 1

    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [phrase for phrase, _ in ranked[:limit]]


def summarize_messages(messages: list[dict]) -> dict:
    """提取用于 dry-run 和 persona 草案的摘要信息。"""
    extracted = qq_chat_parser.extract_key_content(messages)
    top_phrases = extract_top_phrases(messages)

    summary_parts = [f"共 {len(messages)} 条消息"]
    if extracted["interactive_messages"]:
        summary_parts.append(f"{len(extracted['interactive_messages'])} 条互动消息")
    if extracted["long_messages"]:
        summary_parts.append(f"{len(extracted['long_messages'])} 条长消息")
    if top_phrases:
        summary_parts.append(f"高频短句：{' / '.join(top_phrases)}")

    return {
        "message_count": len(messages),
        "interactive_count": len(extracted["interactive_messages"]),
        "long_count": len(extracted["long_messages"]),
        "top_phrases": top_phrases,
        "summary": "；".join(summary_parts),
    }


def build_layer_zero_rules(message_count: int, interactive_count: int, long_count: int, top_phrases: list[str], tags: list[str]) -> list[str]:
    """构造 Layer 0 规则。"""
    rules: list[str] = []

    if message_count >= 100:
        rules.append("在群聊里非常活跃，经常连续接话，同一轮话题里会持续刷存在感。")
    elif message_count >= 50:
        rules.append("在群聊里比较活跃，常常会顺着当前话题持续参与。")
    elif message_count >= 20:
        rules.append("在群聊里有稳定发言，不是只偶尔冒泡一下的路过型成员。")
    else:
        rules.append("当前样本量有限，但能看出你会在熟悉话题里接话。")

    if interactive_count > 0:
        rules.append("遇到别人点名、回复或接梗时，你通常会顺势回应，把对话往前推。")

    if long_count > 0:
        rules.append("当话题需要解释、吐槽或表达观点时，你会发相对更长的消息把话说完整。")

    if top_phrases:
        joined = "、".join(f"“{phrase}”" for phrase in top_phrases)
        rules.append(f"你有明显的口头重复倾向，像 {joined} 这类短句会反复出现。")

    for tag in tags:
        rule = TAG_RULES.get(tag)
        if rule and rule not in rules:
            rules.append(rule)

    while len(rules) < 3:
        rules.append("群聊语气偏口语化，会优先说熟悉、顺手、带一点生活味的话。")

    return rules[:5]


def build_examples(top_phrases: list[str]) -> dict[str, str]:
    """构造 Layer 2 示例回复。"""
    default_phrase = top_phrases[0] if top_phrases else "来了"

    return {
        "funny": f"{default_phrase}，这波有点东西。",
        "question": "我先接一句，等我想清楚再补完整点。",
        "mention": f"{default_phrase}，叫我干嘛？",
        "topic": "这话题我能接，先说我第一反应。",
        "argument": "先别急，我把我看到的点摆出来。",
    }


def build_persona_content(candidate: dict) -> str:
    """从批量候选摘要生成基础 persona.md 内容。"""
    name = candidate["name"]
    profile = candidate["meta"].get("profile", {})
    tags = candidate["meta"].get("personality", [])
    summary = candidate["analysis"]
    top_phrases = summary["top_phrases"]
    examples = build_examples(top_phrases)
    layer_zero = build_layer_zero_rules(
        summary["message_count"],
        summary["interactive_count"],
        summary["long_count"],
        top_phrases,
        tags,
    )

    identity_lines = [f"你是 {name}。"]
    if profile.get("age"):
        identity_lines.append(f"你 {profile['age']} 岁。")
    if profile.get("gender"):
        identity_lines.append(f"你是{profile['gender']}。")
    if profile.get("occupation"):
        identity_lines.append(f"你的职业是 {profile['occupation']}。")
    if profile.get("hobbies"):
        identity_lines.append(f"你喜欢 {profile['hobbies']}。")
    if profile.get("mbti"):
        identity_lines.append(f"MBTI {profile['mbti']}。")
    identity_lines.append(f"自动批量分析摘要：{candidate['summary']}。")

    catchphrases = "，".join(f"“{phrase}”" for phrase in top_phrases) if top_phrases else "（样本不足，待补充）"
    style_tags = "、".join(tags) if tags else "（暂无手动标签）"

    if summary["message_count"] >= 100:
        activity = "你在群里非常活跃，经常刷到存在感。"
    elif summary["message_count"] >= 50:
        activity = "你在群里比较活跃，会稳定参与当前话题。"
    elif summary["message_count"] >= 20:
        activity = "你在群里有持续发言，熟悉的话题会明显更投入。"
    else:
        activity = "当前样本偏少，你的完整聊天习惯还需要继续补充。"

    response_speed = "遇到别人接话或点名时通常会较快回应。" if summary["interactive_count"] else "互动样本有限，回复节奏暂按普通群成员处理。"
    controversy = "会继续接话表达自己的判断。" if summary["long_count"] else "更像是点到为止，不一定会长篇争下去。"

    return f"""# {name} — Persona

---

## Layer 0：核心性格（最高优先级，任何情况下不得违背）

{chr(10).join(f"- {rule}" for rule in layer_zero)}

---

## Layer 1：身份

{chr(10).join(identity_lines)}

---

## Layer 2：表达风格

### 口头禅与高频词
你的口头禅：{catchphrases}
你的风格标签：{style_tags}

### 说话方式
你说话偏口语化，常用短句直接接当前话题。
遇到熟悉话题时会把节奏往前推，不会故意装得很正式。
如果样本不足，这一层属于自动推断，后续可以继续用真实聊天记录修正。

### 你会怎么说（直接给例子，越真实越好）

> 有人在群里发了一个搞笑视频：
> 你：{examples['funny']}

> 有人在群里问一个问题：
> 你：{examples['question']}

> 有人在群里@你：
> 你：{examples['mention']}

> 有人在群里讨论你感兴趣的话题：
> 你：{examples['topic']}

> 有人在群里发起争论：
> 你：{examples['argument']}

---

## Layer 3：聊天行为模式

### 活跃程度
{activity}

### 发言时机
你更容易在群聊已经热起来的时候接话，也会在熟悉话题里冒出来补一句。

### 话题参与度
如果当前话题和你已有表达习惯对上，你会明显更愿意多说。

### 互动方式
你会根据别人抛出来的话顺势回应，必要时会连发几句把意思补完整。

### 回应速度
{response_speed}

### 面对争议
{controversy}

---

## Layer 4：兴趣偏好

### 常聊话题
（自动批量分析暂未稳定提取主题词，建议后续补充人工标签或更多原始记录）

### 推荐习惯
更像是先顺着当前群聊节奏接话，而不是一开始就系统推荐东西。

### 专业领域
（暂无稳定证据）

### 娱乐偏好
（暂无稳定证据）

---

## Layer 5：边界与雷区

你不喜欢（有原材料为证）：
- （当前批量模式暂未稳定识别）

你会拒绝：
- （当前批量模式暂未稳定识别）

你会回避的话题：
- （当前批量模式暂未稳定识别）

---

## Correction 记录

（暂无记录）

---

## 行为总原则

在所有交互中：
1. **Layer 0 优先级最高**，任何情况下不得违背
2. 用 Layer 2 的风格说话——不要“跳出角色”变成通用 AI
3. 用 Layer 3 的框架做判断
4. 用 Layer 4 的方式处理兴趣相关话题
5. Correction 层有规则时，优先遵守 Correction 层
"""


def build_candidate_roster(
    messages: list[dict],
    min_messages: int = DEFAULT_MIN_MESSAGES,
    mapping: dict | None = None,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> list[dict]:
    """根据群聊消息构建候选成员清单。"""
    include_set, exclude_set = merge_identifier_filters(mapping, include, exclude)
    grouped = qq_chat_parser.group_messages_by_sender(messages)
    candidates: list[dict] = []

    for sender_key, bucket in grouped.items():
        source_name = str(bucket.get("sender") or sender_key)
        match_keys = {sender_key, source_name}

        if match_keys & exclude_set:
            continue

        member_messages = list(bucket.get("messages", []))
        message_count = len(member_messages)
        explicitly_included = bool(match_keys & include_set)

        if message_count < min_messages and not explicitly_included:
            continue

        alias = resolve_alias(mapping, sender_key, source_name)
        resolved_name = str(alias.get("name") or source_name or sender_key)
        slug = str(alias.get("slug") or skill_writer.slugify(resolved_name))
        profile = dict(alias.get("profile") or {})
        tags = list(alias.get("tags") or [])
        analysis = summarize_messages(member_messages)

        candidate = {
            "sender_key": sender_key,
            "source_name": source_name,
            "name": resolved_name,
            "slug": slug,
            "message_count": message_count,
            "messages": member_messages,
            "analysis": analysis,
            "summary": analysis["summary"],
            "meta": {
                "name": resolved_name,
                "profile": profile,
                "personality": tags,
            },
        }
        candidate["persona_content"] = build_persona_content(candidate)
        candidates.append(candidate)

    candidates.sort(key=lambda item: (-item["message_count"], item["slug"]))
    return candidates


def build_update_patch(candidate: dict) -> str:
    """为已有 skill 生成保守的批量更新补丁。"""
    now = datetime.now().strftime("%Y-%m-%d")
    analysis = candidate.get("analysis") or {}
    top_phrases = list(analysis.get("top_phrases") or [])
    lines = [
        f"## Batch Update {now}",
        "",
        f"- 自动批量分析摘要：{candidate['summary']}",
    ]
    if top_phrases:
        lines.append(f"- 新观察到的高频短句：{'、'.join(top_phrases)}")
    return "\n".join(lines)


def apply_candidates(base_dir: Path, candidates: list[dict], on_exists: str = DEFAULT_ON_EXISTS) -> dict:
    """将候选成员批量写入 skill 目录。"""
    if on_exists not in {"skip", "update", "fail"}:
        raise ValueError(f"不支持的 on_exists 策略：{on_exists}")

    result = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "results": [],
    }

    base_dir.mkdir(parents=True, exist_ok=True)

    for candidate in candidates:
        slug = candidate["slug"]
        skill_dir = base_dir / slug

        if skill_dir.exists():
            if on_exists == "skip":
                result["skipped"] += 1
                result["results"].append({"slug": slug, "status": "skipped"})
                continue
            if on_exists == "fail":
                raise FileExistsError(f"Skill 已存在：{skill_dir}")

            new_version = skill_writer.update_skill(
                skill_dir,
                persona_patch=build_update_patch(candidate),
            )
            result["updated"] += 1
            result["results"].append({"slug": slug, "status": "updated", "version": new_version})
            continue

        skill_writer.create_skill(
            base_dir,
            slug,
            candidate["meta"],
            candidate["persona_content"],
        )
        result["created"] += 1
        result["results"].append({"slug": slug, "status": "created"})

    return result


def render_preview(candidates: list[dict]) -> str:
    """将 dry-run 候选列表格式化为人类可读输出。"""
    if not candidates:
        return "没有命中可批量创建的候选成员。"

    lines = [f"候选成员 {len(candidates)} 人：", ""]
    for item in candidates:
        lines.append(f"- {item['name']} [{item['slug']}]")
        lines.append(f"  原始发送者：{item['source_name']} / 键：{item['sender_key']}")
        lines.append(f"  消息数：{item['message_count']}")
        lines.append(f"  摘要：{item['summary']}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main() -> None:
    ensure_utf8_stdio()

    parser = argparse.ArgumentParser(description="批量分析群聊并生成群友 Skill")
    parser.add_argument("--file", required=True, help="输入群聊记录（.json 或 .txt）")
    parser.add_argument("--base-dir", default="./pigs", help="输出目录（默认：./pigs）")
    parser.add_argument("--mapping", help="批量映射 JSON 文件路径")
    parser.add_argument("--min-messages", type=int, help="最小发言数阈值")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default=DEFAULT_MODE, help="运行模式")
    parser.add_argument("--on-exists", choices=["skip", "update", "fail"], default=DEFAULT_ON_EXISTS, help="已存在 skill 的处理策略")
    parser.add_argument("--include", action="append", default=[], help="显式包含的 sender_key 或 source_name，可重复")
    parser.add_argument("--exclude", action="append", default=[], help="显式排除的 sender_key 或 source_name，可重复")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")

    args = parser.parse_args()

    mapping = load_mapping(args.mapping)
    min_messages = resolve_min_messages(args.min_messages, mapping)
    messages = load_messages(args.file)
    candidates = build_candidate_roster(
        messages,
        min_messages=min_messages,
        mapping=mapping,
        include=args.include,
        exclude=args.exclude,
    )

    if args.mode == "dry-run":
        payload = {
            "mode": "dry-run",
            "min_messages": min_messages,
            "candidates": [
                {
                    "sender_key": item["sender_key"],
                    "source_name": item["source_name"],
                    "name": item["name"],
                    "slug": item["slug"],
                    "message_count": item["message_count"],
                    "summary": item["summary"],
                }
                for item in candidates
            ],
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(render_preview(candidates))
        return

    result = apply_candidates(Path(args.base_dir), candidates, on_exists=args.on_exists)
    payload = {
        "mode": "apply",
        "min_messages": min_messages,
        "created": result["created"],
        "updated": result["updated"],
        "skipped": result["skipped"],
        "results": result["results"],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"批量处理完成：创建 {result['created']}，更新 {result['updated']}，跳过 {result['skipped']}")
    for item in result["results"]:
        print(f"- {item['slug']}: {item['status']}")


if __name__ == "__main__":
    main()
