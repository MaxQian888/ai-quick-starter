#!/usr/bin/env python3
"""
QQ群聊天记录解析器

支持的导出格式：
1. QQ官方导出（群聊记录）：通常为TXT格式，每条消息包含时间、发送人、内容
2. 第三方工具导出的JSON格式

用法：
    python qq_chat_parser.py --file messages.txt --target "小明" --output output.txt
    python qq_chat_parser.py --file messages.json --target "小明" --output output.txt
"""

import json
import re
import sys
import argparse
from pathlib import Path


PLACEHOLDER_EXACT = {
    "[图片]",
    "[文件]",
    "[撤回了一条消息]",
    "[语音]",
    "[表情]",
    "[视频]",
}

PLACEHOLDER_PATTERNS = (
    re.compile(r"^\[图片(?::.+)?\]$"),
    re.compile(r"^\[文件(?::.+)?\]$"),
    re.compile(r"^\[语音(?::.+)?\]$"),
    re.compile(r"^\[视频(?::.+)?\]$"),
    re.compile(r"^\[表情[^\]]*\]$"),
)


def is_placeholder_message(content: str) -> bool:
    """判断是否为无有效文本信息的占位消息。"""
    stripped = (content or "").strip()
    if not stripped:
        return True
    if stripped in PLACEHOLDER_EXACT:
        return True
    return any(pattern.match(stripped) for pattern in PLACEHOLDER_PATTERNS)


def _extract_sender_fields(msg: dict) -> tuple[str, str]:
    """从多种 JSON 导出结构中提取发送者显示名和稳定标识。"""
    sender_obj = msg.get("sender")
    if isinstance(sender_obj, dict):
        sender_name = (
            sender_obj.get("name")
            or sender_obj.get("nickname")
            or sender_obj.get("uin")
            or sender_obj.get("uid")
            or ""
        )
        sender_id = (
            sender_obj.get("uid")
            or sender_obj.get("uin")
            or sender_name
            or ""
        )
        return str(sender_name), str(sender_id)

    sender_name = (
        msg.get("sender")
        or msg.get("from")
        or msg.get("user_name")
        or msg.get("nickname")
        or ""
    )
    sender_id = (
        msg.get("sender_id")
        or msg.get("uid")
        or msg.get("uin")
        or sender_name
        or ""
    )
    return str(sender_name), str(sender_id)


def _extract_message_text(msg: dict) -> str:
    """从多种 JSON 结构中提取文本消息。"""
    content = (
        msg.get("content")
        or msg.get("text")
        or msg.get("message")
        or msg.get("body")
        or ""
    )

    if isinstance(content, dict):
        return str(
            content.get("text")
            or content.get("content")
            or content.get("raw")
            or ""
        )
    if isinstance(content, list):
        return " ".join(
            c.get("text", "") if isinstance(c, dict) else str(c)
            for c in content
        ).strip()
    return str(content).strip()


def normalize_qq_json_message(msg: dict) -> dict | None:
    """将不同 JSON 导出格式归一化为统一消息结构。"""
    if not isinstance(msg, dict):
        return None

    if msg.get("system") is True:
        return None
    if msg.get("recalled") is True:
        return None

    sender_name, sender_id = _extract_sender_fields(msg)
    content = _extract_message_text(msg)
    timestamp = (
        msg.get("timestamp")
        or msg.get("time")
        or msg.get("create_time")
        or ""
    )

    if not sender_name and not sender_id:
        return None
    if is_placeholder_message(content):
        return None

    return {
        "sender": sender_name or sender_id,
        "sender_id": sender_id or sender_name,
        "content": content,
        "timestamp": str(timestamp),
    }


def matches_target(message: dict, target_name: str) -> bool:
    """判断消息是否匹配目标发送者。"""
    if not target_name:
        return True

    target = str(target_name)
    sender = str(message.get("sender", ""))
    sender_id = str(message.get("sender_id", ""))
    return target in sender or target in sender_id


def group_messages_by_sender(messages: list[dict]) -> dict[str, dict]:
    """按发送者聚合消息，优先使用 sender_id 作为稳定键。"""
    grouped: dict[str, dict] = {}

    for msg in messages:
        key = str(msg.get("sender_id") or msg.get("sender") or "").strip()
        if not key:
            continue

        bucket = grouped.setdefault(
            key,
            {
                "sender": msg.get("sender", key),
                "sender_id": msg.get("sender_id", key),
                "messages": [],
            },
        )
        bucket["messages"].append(msg)

    return grouped


def parse_qq_txt(file_path: str, target_name: str) -> list[dict]:
    """解析QQ官方导出的TXT格式消息"""
    messages = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 匹配QQ导出的格式：
    # 2024-01-01 10:00:00 小明
    # 消息内容
    # 空行
    pattern = re.compile(
        r"^(?P<time>\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{2}:\d{2})\s+(?P<sender>.+)$"
    )

    current_sender = ""
    current_time = ""
    current_content = []

    for line in lines:
        line = line.strip()
        if not line:
            # 空行，结束当前消息
            if current_sender and current_content:
                content = "\n".join(current_content)
                if target_name and target_name not in current_sender:
                    current_content = []
                    continue
                if content:
                    messages.append({
                        "sender": current_sender,
                        "content": content,
                        "timestamp": current_time,
                    })
                current_content = []
            continue

        m = pattern.match(line)
        if m:
            # 新消息开始
            if current_sender and current_content:
                # 保存上一条消息
                content = "\n".join(current_content)
                if target_name and target_name not in current_sender:
                    current_content = []
                    current_sender = m.group("sender").strip()
                    current_time = m.group("time").strip()
                    continue
                if content:
                    messages.append({
                        "sender": current_sender,
                        "content": content,
                        "timestamp": current_time,
                    })
            current_sender = m.group("sender").strip()
            current_time = m.group("time").strip()
            current_content = []
        else:
            # 消息内容续行
            current_content.append(line)

    # 处理最后一条消息
    if current_sender and current_content:
        content = "\n".join(current_content)
        if not target_name or target_name in current_sender:
            if content:
                messages.append({
                    "sender": current_sender,
                    "content": content,
                    "timestamp": current_time,
                })

    return messages


def parse_qq_json(file_path: str, target_name: str) -> list[dict]:
    """解析第三方工具导出的JSON格式消息"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = []

    # 兼容多种 JSON 结构
    if isinstance(data, list):
        raw_messages = data
    elif isinstance(data, dict):
        # 可能在 data.messages 或 data.records 等字段下
        raw_messages = (
            data.get("messages")
            or data.get("records")
            or data.get("data")
            or []
        )
    else:
        return []

    for msg in raw_messages:
        normalized = normalize_qq_json_message(msg)
        if not normalized:
            continue

        if not matches_target(normalized, target_name):
            continue

        messages.append(normalized)

    return messages


def extract_key_content(messages: list[dict]) -> dict:
    """
    对消息进行分类提取，区分：
    - 长消息（>50字）：可能包含观点、方案、技术判断
    - 互动类消息：包含@、回复等
    - 日常沟通：其他消息
    """
    long_messages = []
    interactive_messages = []
    daily_messages = []

    interactive_keywords = ["@", "回复", "引用", "转发"]

    for msg in messages:
        content = msg["content"]

        if len(content) > 50:
            long_messages.append(msg)
        elif any(kw in content for kw in interactive_keywords):
            interactive_messages.append(msg)
        else:
            daily_messages.append(msg)

    return {
        "long_messages": long_messages,
        "interactive_messages": interactive_messages,
        "daily_messages": daily_messages,
        "total_count": len(messages),
    }


def format_output(target_name: str, extracted: dict) -> str:
    """格式化输出，供 AI 分析使用"""
    lines = [
        f"# QQ群聊天记录提取结果",
        f"目标人物：{target_name}",
        f"总消息数：{extracted['total_count']}",
        "",
        "---",
        "",
        "## 长消息（观点/方案类，权重最高）",
        "",
    ]

    for msg in extracted["long_messages"]:
        ts = f"[{msg['timestamp']}] " if msg["timestamp"] else ""
        lines.append(f"{ts}{msg['content']}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 互动类消息",
        "",
    ]

    for msg in extracted["interactive_messages"]:
        ts = f"[{msg['timestamp']}] " if msg["timestamp"] else ""
        lines.append(f"{ts}{msg['content']}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 日常沟通（风格参考）",
        "",
    ]

    # 日常消息只取前 100 条，避免太长
    for msg in extracted["daily_messages"][:100]:
        ts = f"[{msg['timestamp']}] " if msg["timestamp"] else ""
        lines.append(f"{ts}{msg['content']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="解析QQ群聊天记录文件")
    parser.add_argument("--file", required=True, help="输入文件路径（.json 或 .txt）")
    parser.add_argument("--target", required=True, help="目标人物姓名（只提取此人发出的消息）")
    parser.add_argument("--output", default=None, help="输出文件路径（默认打印到 stdout）")

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误：文件不存在 {file_path}", file=sys.stderr)
        sys.exit(1)

    # 根据文件类型选择解析器
    if file_path.suffix.lower() == ".json":
        messages = parse_qq_json(str(file_path), args.target)
    else:
        messages = parse_qq_txt(str(file_path), args.target)

    if not messages:
        print(f"警告：未找到 '{args.target}' 发出的消息", file=sys.stderr)
        print("提示：请检查目标姓名是否与文件中的发送人名称一致", file=sys.stderr)

    extracted = extract_key_content(messages)
    output = format_output(args.target, extracted)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"已输出到 {args.output}，共 {len(messages)} 条消息")
    else:
        print(output)


if __name__ == "__main__":
    main()
