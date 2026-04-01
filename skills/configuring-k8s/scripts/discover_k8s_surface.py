#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path


SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    "artifacts",
}
SKIP_PREFIXES = ("_tmp", ".uv-", ".venv")
KUSTOMIZATION_NAMES = {"kustomization.yaml", "kustomization.yml", "kustomization"}
TEXT_EXTENSIONS = {".yaml", ".yml", ".json"}
ENTRYPOINT_PRIORITY = {
    "kubeconfig": 100,
    "helmfile": 95,
    "helm-chart": 90,
    "kustomization": 85,
    "helm-values": 80,
    "manifest": 60,
}


@dataclass
class ToolchainRecord:
    name: str
    evidence: list[str]


@dataclass
class EntrypointRecord:
    path: str
    kind: str
    reason: str


@dataclass
class FileRecord:
    path: str
    type: str
    toolchain: str
    kind: str | None
    api_version: str | None
    name: str | None
    namespace: str | None
    templated: bool
    reason: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a repository and summarize Kubernetes configuration entrypoints."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def should_skip_dir(name: str) -> bool:
    return (
        name in SKIP_DIR_NAMES
        or name == "tmp"
        or name.startswith(SKIP_PREFIXES)
        or name.endswith(".tmp-tests")
    )


def relative_to_root(path: Path, root: Path) -> str:
    try:
        value = str(path.relative_to(root))
    except ValueError:
        value = str(path)
    return value.replace("\\", "/")


def iter_candidate_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if not should_skip_dir(name)]
        current_path = Path(current_root)
        for filename in filenames:
            path = current_path / filename
            lower_name = filename.lower()
            lower_parts = tuple(part.lower() for part in path.parts)
            if lower_name in {"chart.yaml", "chart.yml", "helmfile.yaml", "helmfile.yml"}:
                candidates.append(path)
                continue
            if lower_name in KUSTOMIZATION_NAMES:
                candidates.append(path)
                continue
            if (
                lower_name.endswith(".kubeconfig")
                or lower_name.startswith("kubeconfig")
                or lower_name in {"config", "config.yaml", "config.yml"}
            ) and path.suffix.lower() in {"", ".yaml", ".yml", ".kubeconfig"}:
                candidates.append(path)
                continue
            if lower_name == "config" and ".kube" in lower_parts:
                candidates.append(path)
                continue
            if path.suffix.lower() in TEXT_EXTENSIONS:
                candidates.append(path)
    return sorted(candidates)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def find_scalar(text: str, key: str) -> str | None:
    patterns = [
        rf'^\s*{re.escape(key)}\s*:\s*"?([^\n"#]+?)"?\s*$',
        rf'"{re.escape(key)}"\s*:\s*"([^"]+)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def find_metadata_field(text: str, field: str) -> str | None:
    yaml_match = re.search(
        rf"(?ms)^\s*metadata\s*:\s*\n(?P<body>(?:^[ \t].*\n?)*)",
        text,
    )
    if yaml_match:
        body = yaml_match.group("body")
        match = re.search(
            rf'^\s*{re.escape(field)}\s*:\s*"?([^\n"#]+?)"?\s*$',
            body,
            re.MULTILINE,
        )
        if match:
            return match.group(1).strip()

    json_match = re.search(
        rf'"metadata"\s*:\s*\{{(?P<body>.*?)\}}',
        text,
        re.DOTALL,
    )
    if json_match:
        match = re.search(
            rf'"{re.escape(field)}"\s*:\s*"([^"]+)"',
            json_match.group("body"),
        )
        if match:
            return match.group(1).strip()
    return None


def detect_chart_roots(paths: list[Path]) -> set[Path]:
    return {path.parent for path in paths if path.name.lower() in {"chart.yaml", "chart.yml"}}


def detect_kustomization_roots(paths: list[Path]) -> set[Path]:
    return {path.parent for path in paths if path.name.lower() in KUSTOMIZATION_NAMES}


def belongs_to_chart(path: Path, chart_roots: set[Path]) -> bool:
    return any(root in path.parents or path.parent == root for root in chart_roots)


def belongs_to_kustomization(path: Path, kustomization_roots: set[Path]) -> bool:
    return any(root in path.parents for root in kustomization_roots)


def classify_file(
    path: Path,
    root: Path,
    chart_roots: set[Path],
    kustomization_roots: set[Path],
) -> FileRecord | None:
    lower_name = path.name.lower()
    relative_path = relative_to_root(path, root)
    text = read_text(path)
    templated = "{{" in text or "{%" in text

    if lower_name in {"chart.yaml", "chart.yml"}:
        return FileRecord(
            path=relative_path,
            type="helm-chart",
            toolchain="helm",
            kind=None,
            api_version=find_scalar(text, "apiVersion"),
            name=find_scalar(text, "name"),
            namespace=None,
            templated=templated,
            reason="Helm chart entrypoint.",
        )

    if lower_name.startswith("helmfile.") and path.suffix.lower() in {".yaml", ".yml"}:
        return FileRecord(
            path=relative_path,
            type="helmfile",
            toolchain="helmfile",
            kind=None,
            api_version=None,
            name=None,
            namespace=None,
            templated=templated,
            reason="Helmfile controls one or more Helm releases.",
        )

    if lower_name in KUSTOMIZATION_NAMES:
        return FileRecord(
            path=relative_path,
            type="kustomization",
            toolchain="kustomize",
            kind=None,
            api_version=None,
            name=None,
            namespace=find_scalar(text, "namespace"),
            templated=templated,
            reason="Kustomize entrypoint.",
        )

    if lower_name == "config" and ".kube" in {part.lower() for part in path.parts}:
        return FileRecord(
            path=relative_path,
            type="kubeconfig",
            toolchain="kubeconfig",
            kind=None,
            api_version=find_scalar(text, "apiVersion"),
            name=None,
            namespace=find_scalar(text, "namespace"),
            templated=templated,
            reason="Kubeconfig file for cluster access and contexts.",
        )

    if (
        lower_name.endswith(".kubeconfig")
        or lower_name.startswith("kubeconfig")
        or (lower_name in {"config.yaml", "config.yml"} and "kube" in relative_path.lower())
    ):
        if "clusters:" in text or "contexts:" in text or find_scalar(text, "current-context"):
            return FileRecord(
                path=relative_path,
                type="kubeconfig",
                toolchain="kubeconfig",
                kind=None,
                api_version=find_scalar(text, "apiVersion"),
                name=None,
                namespace=find_scalar(text, "namespace"),
                templated=templated,
                reason="Kubeconfig-like file for cluster access and contexts.",
            )

    if lower_name.startswith("values") and path.suffix.lower() in {".yaml", ".yml"} and belongs_to_chart(path, chart_roots):
        return FileRecord(
            path=relative_path,
            type="helm-values",
            toolchain="helm",
            kind=None,
            api_version=None,
            name=None,
            namespace=find_scalar(text, "namespace"),
            templated=templated,
            reason="Helm values file likely drives environment-specific settings.",
        )

    api_version = find_scalar(text, "apiVersion")
    kind = find_scalar(text, "kind")
    name = find_metadata_field(text, "name")
    namespace = find_metadata_field(text, "namespace")

    if kind or api_version or templated:
        if belongs_to_chart(path, chart_roots):
            toolchain = "helm"
            record_type = "helm-template"
            reason = "Helm-managed manifest or template file."
        elif belongs_to_kustomization(path, kustomization_roots):
            toolchain = "kustomize"
            record_type = "manifest"
            reason = "Manifest owned by a nearby Kustomize entrypoint."
        else:
            toolchain = "raw-manifest"
            record_type = "manifest"
            reason = "Manifest-like file with Kubernetes fields."
        return FileRecord(
            path=relative_path,
            type=record_type,
            toolchain=toolchain,
            kind=kind,
            api_version=api_version,
            name=name,
            namespace=namespace,
            templated=templated,
            reason=reason,
        )

    return None


def collect_toolchains(records: list[FileRecord]) -> list[ToolchainRecord]:
    evidence_map: dict[str, list[str]] = {}
    for record in records:
        evidence_map.setdefault(record.toolchain, [])
        if len(evidence_map[record.toolchain]) < 4:
            evidence_map[record.toolchain].append(record.path)
    return [
        ToolchainRecord(name=name, evidence=evidence)
        for name, evidence in sorted(evidence_map.items())
    ]


def build_entrypoints(records: list[FileRecord]) -> list[EntrypointRecord]:
    entries: dict[str, EntrypointRecord] = {}
    for record in records:
        if record.type not in ENTRYPOINT_PRIORITY:
            continue
        reason = record.reason
        if record.type == "manifest" and record.kind:
            reason = f"{record.kind} manifest with direct Kubernetes fields."
        candidate = EntrypointRecord(path=record.path, kind=record.type, reason=reason)
        current = entries.get(record.path)
        if current is None or ENTRYPOINT_PRIORITY[record.type] > ENTRYPOINT_PRIORITY[current.kind]:
            entries[record.path] = candidate
    return sorted(
        entries.values(),
        key=lambda item: (-ENTRYPOINT_PRIORITY[item.kind], item.path),
    )


def build_read_order(records: list[FileRecord]) -> list[str]:
    priority = {
        "kubeconfig": 100,
        "helmfile": 95,
        "helm-chart": 90,
        "kustomization": 85,
        "helm-values": 80,
        "helm-template": 70,
        "manifest": 60,
    }
    ranked = sorted(records, key=lambda item: (-priority.get(item.type, 0), item.path))
    return [record.path for record in ranked[:12]]


def build_risks(records: list[FileRecord], toolchains: list[ToolchainRecord]) -> list[str]:
    risks: set[str] = set()
    toolchain_names = {record.name for record in toolchains}
    if len(toolchain_names) > 1:
        risks.add("Multiple Kubernetes config toolchains detected. Preserve the existing ownership boundary.")
    if any(record.kind == "Secret" or "secret" in record.path.lower() for record in records):
        risks.add("Secret-bearing configuration detected. Review exposure risk before editing or committing values.")
    if any(record.templated for record in records):
        risks.add("Templated files detected. Render with Helm or Kustomize before claiming the final manifest is correct.")
    if not records:
        risks.add("No obvious Kubernetes configuration files were detected. Manual inspection is required.")
    return sorted(risks)


def inspect_repository(root: Path) -> dict[str, object]:
    candidate_paths = iter_candidate_files(root)
    chart_roots = detect_chart_roots(candidate_paths)
    kustomization_roots = detect_kustomization_roots(candidate_paths)
    records = [
        record
        for path in candidate_paths
        if (record := classify_file(path, root, chart_roots, kustomization_roots))
    ]
    toolchains = collect_toolchains(records)
    entrypoints = build_entrypoints(records)
    payload = {
        "project_root": str(root),
        "toolchains": [asdict(record) for record in toolchains],
        "entrypoints": [asdict(record) for record in entrypoints],
        "files": [asdict(record) for record in records],
        "suggested_read_order": build_read_order(records),
        "risks": build_risks(records, toolchains),
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    payload = inspect_repository(root)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Project root: {payload['project_root']}")
        print("Toolchains:")
        for toolchain in payload["toolchains"]:
            print(f"  - {toolchain['name']}: {', '.join(toolchain['evidence'])}")
        print("Entrypoints:")
        for entrypoint in payload["entrypoints"]:
            print(f"  - {entrypoint['path']} ({entrypoint['kind']})")
        if payload["risks"]:
            print("Risks:")
            for risk in payload["risks"]:
                print(f"  - {risk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
