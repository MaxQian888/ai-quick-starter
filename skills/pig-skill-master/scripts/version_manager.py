#!/usr/bin/env python3
"""
版本管理器

负责 Skill 文件的版本存档、回滚和清理。

用法：
    python version_manager.py --action backup --slug xiao-ming --base-dir ./pigs
    python version_manager.py --action list --slug xiao-ming --base-dir ./pigs
    python version_manager.py --action rollback --slug xiao-ming --version v2 --base-dir ./pigs
"""

from __future__ import annotations

import json
import shutil
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import skill_writer  # type: ignore  # noqa: E402

MAX_VERSIONS = 10  # 最多保留的版本数


def backup_current_version(skill_dir: Path, version_name: Optional[str] = None) -> str:
    """将当前 persona/skill 内容存档到 versions 目录。"""
    meta_path = skill_dir / "meta.json"
    version = version_name

    if version is None and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        version = meta.get("version")

    if not version:
        version = datetime.now(timezone.utc).strftime("snapshot-%Y%m%d-%H%M%S")

    backup_dir = skill_dir / "versions" / version
    backup_dir.mkdir(parents=True, exist_ok=True)

    for fname in ("SKILL.md", "persona.md", "persona-skill.md", "meta.json"):
        src = skill_dir / fname
        if src.exists():
            shutil.copy2(src, backup_dir / fname)

    return version


def list_versions(skill_dir: Path) -> list:
    """列出所有历史版本"""
    versions_dir = skill_dir / "versions"
    if not versions_dir.exists():
        return []

    versions = []
    for v_dir in sorted(versions_dir.iterdir()):
        if not v_dir.is_dir():
            continue

        # 从目录名解析版本号
        version_name = v_dir.name

        # 获取存档时间（用目录修改时间近似）
        mtime = v_dir.stat().st_mtime
        archived_at = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")

        # 统计文件
        files = [f.name for f in v_dir.iterdir() if f.is_file()]

        versions.append({
            "version": version_name,
            "archived_at": archived_at,
            "files": files,
            "path": str(v_dir),
        })

    return versions


def rollback(skill_dir: Path, target_version: str) -> bool:
    """回滚到指定版本"""
    version_dir = skill_dir / "versions" / target_version

    if not version_dir.exists():
        print(f"错误：版本 {target_version} 不存在", file=sys.stderr)
        return False

    # 先存档当前版本
    meta_path = skill_dir / "meta.json"
    current_version = "v?"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        current_version = meta.get("version", "v?")
        backup_current_version(skill_dir, f"{current_version}-before-rollback")

    # 从目标版本恢复文件
    restored_files = []
    for fname in ("SKILL.md", "persona.md", "persona-skill.md"):
        src = version_dir / fname
        if src.exists():
            shutil.copy2(src, skill_dir / fname)
            restored_files.append(fname)

    # 更新 meta
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["version"] = target_version + "_restored"
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        meta["rollback_from"] = current_version
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"已回滚到 {target_version}，恢复文件：{', '.join(restored_files)}")
    return True


def cleanup_old_versions(skill_dir: Path, max_versions: int = MAX_VERSIONS):
    """清理超出限制的旧版本"""
    versions_dir = skill_dir / "versions"
    if not versions_dir.exists():
        return

    # 按版本号排序，保留最新的 max_versions 个
    version_dirs = sorted(
        [d for d in versions_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
    )

    to_delete = version_dirs[:-max_versions] if len(version_dirs) > max_versions else []

    for old_dir in to_delete:
        shutil.rmtree(old_dir)
        print(f"已清理旧版本：{old_dir.name}")


def rewrite_persona_name(persona_content: str, old_names: list[str], new_name: Optional[str]) -> str:
    """在 canonical persona 中同步基础名字字段。"""
    if not new_name:
        return persona_content

    updated = persona_content
    for old_name in old_names:
        if not old_name or old_name == new_name:
            continue
        updated = updated.replace(f"# {old_name} — Persona", f"# {new_name} — Persona", 1)
        updated = updated.replace(f"你是 {old_name}。", f"你是 {new_name}。", 1)
    return updated


def rename_skill(skill_dir: Path, new_slug: str, new_name: Optional[str] = None) -> Path:
    """安全迁移 skill slug，并重写依赖 slug 的生成文件。"""
    new_slug = (new_slug or "").strip()
    if not new_slug:
        raise ValueError("new_slug 不能为空")

    base_dir = skill_dir.parent
    old_slug = skill_dir.name
    target_dir = base_dir / new_slug

    if target_dir.exists() and target_dir != skill_dir:
        raise FileExistsError(f"目标目录已存在：{target_dir}")

    meta_path = skill_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"找不到 meta.json：{meta_path}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    old_name = meta.get("name")
    old_names = []
    for candidate in (old_name, meta.get("renamed_from")):
        if candidate and candidate not in old_names:
            old_names.append(candidate)
    current_version = meta.get("version", "v?")
    backup_current_version(skill_dir, f"{current_version}-before-rename")

    persona_path = skill_dir / "persona.md"
    persona_content = persona_path.read_text(encoding="utf-8") if persona_path.exists() else ""
    persona_content = rewrite_persona_name(persona_content, old_names, new_name)

    if target_dir != skill_dir:
        skill_dir.rename(target_dir)

    previous_renamed_from = meta.get("renamed_from")
    if new_name:
        meta["name"] = new_name
    meta["slug"] = new_slug
    meta["updated_at"] = datetime.now(timezone.utc).isoformat()
    if old_slug != new_slug:
        meta["renamed_from"] = old_slug
    elif previous_renamed_from:
        meta["renamed_from"] = previous_renamed_from

    (target_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (target_dir / "persona.md").write_text(persona_content, encoding="utf-8")
    skill_writer.rewrite_generated_files(target_dir, new_slug, meta, persona_content)
    return target_dir


def rename_from_mapping(base_dir: Path, mapping_path: Path) -> dict:
    """根据 mapping 文件批量迁移已有 skill 的 slug / name。"""
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    aliases = payload.get("aliases", {}) if isinstance(payload, dict) else {}
    if not isinstance(aliases, dict):
        raise ValueError("mapping.aliases 必须是对象")

    result = {"renamed": 0, "skipped": 0, "results": []}

    for _, alias in aliases.items():
        if not isinstance(alias, dict):
            continue

        new_slug = str(alias.get("slug") or "").strip()
        new_name = alias.get("name")
        current_slug = str(
            alias.get("current_slug")
            or alias.get("existing_slug")
            or alias.get("source_name")
            or new_slug
        ).strip()

        if not new_slug or not current_slug:
            result["skipped"] += 1
            result["results"].append({"status": "skipped", "reason": "missing-slug"})
            continue

        skill_dir = base_dir / current_slug
        if not skill_dir.exists():
            result["skipped"] += 1
            result["results"].append({"status": "skipped", "slug": current_slug, "reason": "missing-dir"})
            continue

        meta_path = skill_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        current_name = meta.get("name")

        if current_slug == new_slug and (not new_name or new_name == current_name):
            result["skipped"] += 1
            result["results"].append({"status": "skipped", "slug": current_slug, "reason": "no-change"})
            continue

        new_dir = rename_skill(skill_dir, new_slug, new_name)
        result["renamed"] += 1
        result["results"].append({"status": "renamed", "from": current_slug, "to": new_dir.name})

    return result


def main():
    parser = argparse.ArgumentParser(description="Skill 版本管理器")
    parser.add_argument("--action", required=True, choices=["backup", "list", "rollback", "cleanup", "rename", "rename-from-mapping"])
    parser.add_argument("--slug", help="群友 slug")
    parser.add_argument("--version", help="目标版本号（rollback 时使用）")
    parser.add_argument("--new-slug", help="新 slug（rename 时使用）")
    parser.add_argument("--new-name", help="新昵称（rename 时使用，可选）")
    parser.add_argument("--mapping", help="mapping JSON 路径（rename-from-mapping 时使用）")
    parser.add_argument(
        "--base-dir",
        default="~/.openclaw/workspace/skills/pigs",
        help="群友 Skill 根目录",
    )

    args = parser.parse_args()
    base_dir = Path(args.base_dir).expanduser()
    skill_dir = base_dir / args.slug if args.slug else None

    if args.action != "rename-from-mapping" and not args.slug:
        print("错误：该操作需要 --slug", file=sys.stderr)
        sys.exit(1)

    if args.action != "rename-from-mapping" and skill_dir is not None and not skill_dir.exists():
        print(f"错误：找不到 Skill 目录 {skill_dir}", file=sys.stderr)
        sys.exit(1)

    if args.action == "backup":
        version = backup_current_version(skill_dir)
        print(f"已存档当前版本：{version}")

    elif args.action == "list":
        versions = list_versions(skill_dir)
        if not versions:
            print(f"{args.slug} 暂无历史版本")
        else:
            print(f"{args.slug} 的历史版本：\n")
            for v in versions:
                print(f"  {v['version']}  存档时间: {v['archived_at']}  文件: {', '.join(v['files'])}")

    elif args.action == "rollback":
        if not args.version:
            print("错误：rollback 操作需要 --version", file=sys.stderr)
            sys.exit(1)
        rollback(skill_dir, args.version)

    elif args.action == "cleanup":
        cleanup_old_versions(skill_dir)
        print("清理完成")

    elif args.action == "rename":
        if not args.new_slug:
            print("错误：rename 操作需要 --new-slug", file=sys.stderr)
            sys.exit(1)
        new_dir = rename_skill(skill_dir, args.new_slug, args.new_name)
        print(f"已迁移：{args.slug} -> {new_dir.name}")

    elif args.action == "rename-from-mapping":
        if not args.mapping:
            print("错误：rename-from-mapping 操作需要 --mapping", file=sys.stderr)
            sys.exit(1)
        result = rename_from_mapping(base_dir, Path(args.mapping))
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
