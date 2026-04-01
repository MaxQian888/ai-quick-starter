from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


PROFILE_PATHS = (
    ("windows-powershell-current-user-current-host", Path("Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1")),
    ("windows-powershell-current-user-all-hosts", Path("Documents/WindowsPowerShell/profile.ps1")),
    ("powershell-7-current-user-current-host", Path("Documents/PowerShell/Microsoft.PowerShell_profile.ps1")),
    ("powershell-7-current-user-all-hosts", Path("Documents/PowerShell/profile.ps1")),
)

TERMINAL_PATHS = (
    ("windows-terminal-stable", Path("Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json")),
    ("windows-terminal-preview", Path("Packages/Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe/LocalState/settings.json")),
    ("windows-terminal-unpackaged", Path("Microsoft/Windows Terminal/settings.json")),
)

PATHISH_EXTENSIONS = (
    ".json",
    ".jsonc",
    ".ps1",
    ".psm1",
    ".psd1",
    ".omp.json",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".yaml",
    ".yml",
)

PATH_HINT_KEYS = {
    "backgroundimage",
    "commandline",
    "icon",
    "source",
    "startingdirectory",
}


@dataclass(frozen=True)
class SourceRoots:
    home: Path
    localappdata: Path
    appdata: Path


@dataclass(frozen=True)
class ReferenceContext:
    source_file: Path
    env_map: dict[str, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a PowerShell and Windows Terminal config sync bundle.")
    parser.add_argument("--source-home", required=True)
    parser.add_argument("--source-localappdata", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--json-out")
    parser.add_argument("--markdown-out")
    parser.add_argument("--script-out")
    return parser.parse_args()


def strip_jsonc(text: str) -> str:
    output: list[str] = []
    in_string = False
    string_char = ""
    in_line_comment = False
    in_block_comment = False
    index = 0
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                output.append(char)
            index += 1
            continue
        if in_block_comment:
            if char == "*" and nxt == "/":
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue
        if in_string:
            output.append(char)
            if char == "\\" and nxt:
                output.append(nxt)
                index += 2
                continue
            if char == string_char:
                in_string = False
                string_char = ""
            index += 1
            continue
        if char in ('"', "'"):
            in_string = True
            string_char = char
            output.append(char)
            index += 1
            continue
        if char == "/" and nxt == "/":
            in_line_comment = True
            index += 2
            continue
        if char == "/" and nxt == "*":
            in_block_comment = True
            index += 2
            continue
        output.append(char)
        index += 1
    cleaned = "".join(output)
    return re.sub(r",(\s*[}\]])", r"\1", cleaned)


def load_jsonc(path: Path) -> object:
    return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))


def escape_ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def looks_like_pathish(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered:
        return False
    if value.startswith(("\\\\", "~", "$HOME", "\${HOME}", "$env:", "%")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    if "\\" in value or "/" in value:
        return True
    return lowered.endswith(PATHISH_EXTENSIONS)


def build_env_map(roots: SourceRoots, source_file: Path, profile_vars: dict[str, Path]) -> dict[str, str]:
    env_map = {
        "$HOME": str(roots.home),
        "\${HOME}": str(roots.home),
        "~": str(roots.home),
        "$env:USERPROFILE": str(roots.home),
        "\${env:USERPROFILE}": str(roots.home),
        "%USERPROFILE%": str(roots.home),
        "$env:LOCALAPPDATA": str(roots.localappdata),
        "\${env:LOCALAPPDATA}": str(roots.localappdata),
        "%LOCALAPPDATA%": str(roots.localappdata),
        "$env:APPDATA": str(roots.appdata),
        "\${env:APPDATA}": str(roots.appdata),
        "%APPDATA%": str(roots.appdata),
        "$PSScriptRoot": str(source_file.parent),
        "\${PSScriptRoot}": str(source_file.parent),
    }
    for key, value in profile_vars.items():
        env_map[key] = str(value)
    return env_map


def normalize_reference(raw_reference: str) -> str:
    text = raw_reference.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        text = text[1:-1]
    return text.strip()


def resolve_reference(raw_reference: str, context: ReferenceContext) -> Path | None:
    value = normalize_reference(raw_reference)
    if not value:
        return None
    expanded = value
    for key, replacement in sorted(context.env_map.items(), key=lambda item: len(item[0]), reverse=True):
        expanded = expanded.replace(key, replacement)
    if re.match(r"^[A-Za-z]:[\\/]", expanded) or expanded.startswith("\\\\"):
        return Path(expanded)
    if expanded.startswith(("./", ".\\")):
        return (context.source_file.parent / expanded).resolve(strict=False)
    if "/" in expanded or "\\" in expanded:
        return (context.source_file.parent / expanded).resolve(strict=False)
    return None


def extract_profile_references(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    text = path.read_text(encoding="utf-8")
    references: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add_reference(raw_reference: str, reason: str) -> None:
        normalized = normalize_reference(raw_reference)
        if not normalized or not looks_like_pathish(normalized):
            return
        key = (normalized.lower(), reason)
        if key in seen:
            return
        seen.add(key)
        references.append({"raw_reference": normalized, "reason": reason})

    for match in re.finditer(r"--config\s+(?P<value>(\"[^\"]+\"|'[^']+'|\S+))", text):
        add_reference(match.group("value"), "oh-my-posh-config")
    for match in re.finditer(r"(?m)^\s*\.\s+(?P<value>(\"[^\"]+\"|'[^']+'|\S+))", text):
        add_reference(match.group("value"), "dot-source")
    for match in re.finditer(r"(?P<quote>[\"'])(?P<value>.+?)(?P=quote)", text):
        add_reference(match.group("value"), "quoted-path")

    modules = sorted(set(re.findall(r"(?mi)^\s*Import-Module\s+([A-Za-z0-9_.-]+)", text)))
    return references, modules


def walk_terminal_values(value: object, *, key_path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    items: list[tuple[tuple[str, ...], str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(walk_terminal_values(child, key_path=(*key_path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(walk_terminal_values(child, key_path=(*key_path, str(index))))
    elif isinstance(value, str):
        items.append((key_path, value))
    return items


def extract_terminal_references(path: Path) -> list[dict[str, str]]:
    payload = load_jsonc(path)
    references: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for key_path, value in walk_terminal_values(payload):
        leaf = key_path[-1].lower() if key_path else ""
        if leaf not in PATH_HINT_KEYS and not looks_like_pathish(value):
            continue
        normalized = normalize_reference(value)
        reason = "terminal:" + ".".join(key_path) if key_path else "terminal:value"
        key = (normalized.lower(), reason)
        if key in seen:
            continue
        seen.add(key)
        references.append({"raw_reference": normalized, "reason": reason})
    return references


def detect_profiles(roots: SourceRoots) -> list[dict[str, object]]:
    profiles: list[dict[str, object]] = []
    for name, relative_path in PROFILE_PATHS:
        absolute_path = roots.home / relative_path
        profiles.append({"name": name, "path": str(absolute_path), "exists": absolute_path.exists()})
    return profiles


def detect_terminal_settings(roots: SourceRoots) -> list[dict[str, object]]:
    settings: list[dict[str, object]] = []
    for name, relative_path in TERMINAL_PATHS:
        absolute_path = roots.localappdata / relative_path
        settings.append({"name": name, "path": str(absolute_path), "exists": absolute_path.exists()})
    return settings


def profile_lookup(roots: SourceRoots) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for _, relative_path in PROFILE_PATHS:
        absolute_path = roots.home / relative_path
        if relative_path == Path("Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1"):
            mapping["$PROFILE.CurrentUserCurrentHost"] = absolute_path
        elif relative_path == Path("Documents/WindowsPowerShell/profile.ps1"):
            mapping["$PROFILE.CurrentUserAllHosts"] = absolute_path
    return mapping


def add_discovered_file(
    discovered: dict[str, dict[str, object]],
    *,
    source_path: Path,
    kind: str,
    discovered_from: str,
) -> None:
    key = str(source_path).lower()
    existing = discovered.get(key)
    if existing is None:
        discovered[key] = {
            "source_path": str(source_path),
            "kind": kind,
            "discovered_from": sorted({discovered_from}),
        }
        return
    existing["discovered_from"] = sorted(set(existing["discovered_from"]) | {discovered_from})
    if kind not in str(existing["kind"]).split(","):
        existing["kind"] = str(existing["kind"]) + "," + kind


def build_copy_mappings(
    discovered: dict[str, dict[str, object]],
    roots: SourceRoots,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    copy_mappings: list[dict[str, str]] = []
    manual_review: list[dict[str, str]] = []
    for record in discovered.values():
        source_path = Path(record["source_path"])
        if source_path.is_relative_to(roots.localappdata):
            copy_mappings.append(
                {
                    "source_path": str(source_path),
                    "target_scope": "localappdata",
                    "relative_path": str(source_path.relative_to(roots.localappdata)),
                    "kind": str(record["kind"]),
                }
            )
            continue
        if source_path.is_relative_to(roots.home):
            copy_mappings.append(
                {
                    "source_path": str(source_path),
                    "target_scope": "home",
                    "relative_path": str(source_path.relative_to(roots.home)),
                    "kind": str(record["kind"]),
                }
            )
            continue
        manual_review.append(
            {
                "source_path": str(source_path),
                "reason": "No automatic destination is known because the file is outside the source home and LocalAppData roots.",
                "kind": str(record["kind"]),
            }
        )
    copy_mappings.sort(key=lambda item: (item["target_scope"], item["relative_path"], item["source_path"]))
    manual_review.sort(key=lambda item: item["source_path"])
    return copy_mappings, manual_review


def render_sync_script(copy_mappings: list[dict[str, str]], manual_review: list[dict[str, str]]) -> str:
    lines = [
        "Set-StrictMode -Version Latest",
        '$ErrorActionPreference = "Stop"',
        "",
        "[CmdletBinding(SupportsShouldProcess)]",
        "param(",
        "    [Parameter(Mandatory)]",
        "    [string]$TargetHome,",
        "    [string]$TargetLocalAppData",
        ")",
        "",
        "if (-not $TargetLocalAppData) {",
        "    $TargetLocalAppData = Join-Path $TargetHome 'AppData\\Local'",
        "}",
        "",
        "$CopyMappings = @(",
    ]
    for item in copy_mappings:
        lines.extend(
            [
                "    [pscustomobject]@{",
                f"        SourcePath = {escape_ps(item['source_path'])}",
                f"        TargetScope = {escape_ps(item['target_scope'])}",
                f"        RelativePath = {escape_ps(item['relative_path'])}",
                f"        Kind = {escape_ps(item['kind'])}",
                "    }",
            ]
        )
    lines.extend(["", ")", "", "$ManualReview = @("])
    for item in manual_review:
        lines.extend(
            [
                "    [pscustomobject]@{",
                f"        SourcePath = {escape_ps(item['source_path'])}",
                f"        Reason = {escape_ps(item['reason'])}",
                f"        Kind = {escape_ps(item['kind'])}",
                "    }",
            ]
        )
    lines.extend(
        [
            ")",
            "",
            "foreach ($item in $CopyMappings) {",
            "    if ($item.TargetScope -eq 'home') {",
            "        $targetRoot = $TargetHome",
            "    }",
            "    elseif ($item.TargetScope -eq 'localappdata') {",
            "        $targetRoot = $TargetLocalAppData",
            "    }",
            "    else {",
            '        Write-Warning "Skipping unsupported target scope: $($item.TargetScope)"',
            "        continue",
            "    }",
            "",
            "    $destinationPath = Join-Path $targetRoot $item.RelativePath",
            "    $destinationDir = Split-Path -Parent $destinationPath",
            "    if (-not (Test-Path -LiteralPath $destinationDir)) {",
            "        New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null",
            "    }",
            "",
            '    if ($PSCmdlet.ShouldProcess($destinationPath, "Copy shell config from $($item.SourcePath)")) {',
            "        Copy-Item -LiteralPath $item.SourcePath -Destination $destinationPath -Force",
            "    }",
            "}",
            "",
            "if ($ManualReview.Count -gt 0) {",
            "    Write-Warning 'Manual review items remain. No automatic destination is known for these files:'",
            "    $ManualReview | Format-Table -AutoSize | Out-String | Write-Host",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# PowerShell Terminal Config Sync Bundle",
        "",
        "## Source Roots",
        f"- Home: {payload['source_roots']['home']}",
        f"- LocalAppData: {payload['source_roots']['localappdata']}",
        "",
        "## Profiles",
    ]
    for item in payload["profiles"]:
        lines.append(f"- {item['name']}: {item['path']} ({'exists' if item['exists'] else 'missing'})")
    lines.extend(["", "## Terminal Settings"])
    for item in payload["terminal_settings"]:
        lines.append(f"- {item['name']}: {item['path']} ({'exists' if item['exists'] else 'missing'})")
    lines.extend(["", "## Module References"])
    if payload["module_references"]:
        for item in payload["module_references"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Copy Mappings"])
    if payload["copy_mappings"]:
        for item in payload["copy_mappings"]:
            lines.append(f"- {item['source_path']} -> {item['target_scope']} / {item['relative_path']} ({item['kind']})")
    else:
        lines.append("- None.")
    lines.extend(["", "## Manual Review"])
    if payload["manual_review"]:
        for item in payload["manual_review"]:
            lines.append(f"- {item['source_path']}: {item['reason']}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Unresolved References"])
    if payload["unresolved_references"]:
        for item in payload["unresolved_references"]:
            lines.append(f"- {item['raw_reference']} from {item['source_file']} ({item['reason']})")
    else:
        lines.append("- None.")
    lines.extend(["", "## Blockers"])
    if payload["blockers"]:
        for item in payload["blockers"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Assumptions"])
    if payload["assumptions"]:
        for item in payload["assumptions"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Generated Files",
            f"- JSON bundle: {payload['generated_files']['json_bundle']}",
            f"- Markdown bundle: {payload['generated_files']['markdown_bundle']}",
            f"- Sync script: {payload['generated_files']['sync_script']}",
            "",
        ]
    )
    return "\n".join(lines)


def build_bundle(
    source_home: Path,
    source_localappdata: Path,
    output_dir: Path,
    json_path: Path,
    markdown_path: Path,
    script_path: Path,
) -> dict[str, object]:
    roots = SourceRoots(
        home=source_home.resolve(),
        localappdata=source_localappdata.resolve(),
        appdata=(source_home / "AppData" / "Roaming").resolve(strict=False),
    )
    profiles = detect_profiles(roots)
    terminal_settings = detect_terminal_settings(roots)
    profile_vars = profile_lookup(roots)
    discovered: dict[str, dict[str, object]] = {}
    unresolved_references: list[dict[str, str]] = []
    manual_review_hints: list[dict[str, str]] = []
    module_references: set[str] = set()
    blockers: list[str] = []
    assumptions = [
        "Only existing files under the source home and LocalAppData roots are mapped automatically.",
        "The generated sync script copies files only. Module installation and executable installation stay manual.",
    ]

    existing_profiles = [Path(item["path"]) for item in profiles if item["exists"]]
    if not existing_profiles:
        blockers.append("No PowerShell profile file was found under Documents\\WindowsPowerShell or Documents\\PowerShell.")

    for profile_path in existing_profiles:
        add_discovered_file(discovered, source_path=profile_path, kind="profile", discovered_from=profile_path.name)
        context = ReferenceContext(source_file=profile_path, env_map=build_env_map(roots, profile_path, profile_vars))
        references, modules = extract_profile_references(profile_path)
        module_references.update(modules)
        for item in references:
            resolved = resolve_reference(item["raw_reference"], context)
            if resolved is None:
                unresolved_references.append({"source_file": str(profile_path), "raw_reference": item["raw_reference"], "reason": item["reason"]})
                continue
            if resolved.exists():
                add_discovered_file(discovered, source_path=resolved, kind="profile-dependency", discovered_from=str(profile_path))
            else:
                unresolved_references.append({"source_file": str(profile_path), "raw_reference": item["raw_reference"], "reason": item["reason"]})
                if resolved.is_absolute():
                    manual_review_hints.append(
                        {
                            "source_path": str(resolved),
                            "reason": "No automatic destination is known because the referenced file is outside the source home and LocalAppData roots.",
                            "kind": "missing-profile-dependency",
                        }
                    )

    existing_terminal_settings = [Path(item["path"]) for item in terminal_settings if item["exists"]]
    if not existing_terminal_settings:
        blockers.append("No Windows Terminal settings.json file was found.")
    for terminal_path in existing_terminal_settings:
        add_discovered_file(discovered, source_path=terminal_path, kind="terminal-settings", discovered_from=terminal_path.name)
        context = ReferenceContext(source_file=terminal_path, env_map=build_env_map(roots, terminal_path, profile_vars))
        for item in extract_terminal_references(terminal_path):
            resolved = resolve_reference(item["raw_reference"], context)
            if resolved is None:
                unresolved_references.append({"source_file": str(terminal_path), "raw_reference": item["raw_reference"], "reason": item["reason"]})
                continue
            if resolved.exists():
                add_discovered_file(discovered, source_path=resolved, kind="terminal-asset", discovered_from=str(terminal_path))
            else:
                unresolved_references.append({"source_file": str(terminal_path), "raw_reference": item["raw_reference"], "reason": item["reason"]})
                if resolved.is_absolute():
                    manual_review_hints.append(
                        {
                            "source_path": str(resolved),
                            "reason": "No automatic destination is known because the referenced file is outside the source home and LocalAppData roots.",
                            "kind": "missing-terminal-asset",
                        }
                    )

    copy_mappings, manual_review = build_copy_mappings(discovered, roots)
    manual_lookup = {item["source_path"].lower(): item for item in manual_review}
    for item in manual_review_hints:
        manual_lookup.setdefault(item["source_path"].lower(), item)
    manual_review = sorted(manual_lookup.values(), key=lambda item: item["source_path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    script_path.write_text(render_sync_script(copy_mappings, manual_review), encoding="utf-8")
    payload = {
        "source_roots": {
            "home": str(roots.home),
            "localappdata": str(roots.localappdata),
            "appdata": str(roots.appdata),
        },
        "profiles": profiles,
        "terminal_settings": terminal_settings,
        "module_references": sorted(module_references),
        "copy_mappings": copy_mappings,
        "manual_review": manual_review,
        "unresolved_references": sorted(unresolved_references, key=lambda item: (item["source_file"], item["raw_reference"], item["reason"])),
        "blockers": blockers,
        "assumptions": assumptions,
        "generated_files": {
            "json_bundle": str(json_path),
            "markdown_bundle": str(markdown_path),
            "sync_script": str(script_path),
        },
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    json_path = Path(args.json_out).resolve() if args.json_out else output_dir / "shell-config-sync-bundle.json"
    markdown_path = Path(args.markdown_out).resolve() if args.markdown_out else output_dir / "shell-config-sync-bundle.md"
    script_path = Path(args.script_out).resolve() if args.script_out else output_dir / "sync-shell-config.ps1"
    payload = build_bundle(
        Path(args.source_home),
        Path(args.source_localappdata),
        output_dir,
        json_path,
        markdown_path,
        script_path,
    )
    print(f"JSON_OUT={payload['generated_files']['json_bundle']}")
    print(f"MARKDOWN_OUT={payload['generated_files']['markdown_bundle']}")
    print(f"SYNC_SCRIPT={payload['generated_files']['sync_script']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
