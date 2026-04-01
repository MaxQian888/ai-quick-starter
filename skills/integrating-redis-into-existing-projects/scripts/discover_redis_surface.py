#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".idea",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
SOURCE_EXTENSIONS = {
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".properties",
    ".py",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
MAX_SCAN_FILE_SIZE = 512 * 1024

NODE_FRAMEWORKS = {
    "next": "nextjs",
    "express": "express",
    "@nestjs/core": "nestjs",
    "koa": "koa",
    "fastify": "fastify",
}
NODE_REDIS_DEPENDENCIES = {
    "redis": "client",
    "@redis/client": "client",
    "ioredis": "client",
    "@upstash/redis": "client",
    "bull": "queue",
    "bullmq": "queue",
    "connect-redis": "session",
    "rate-limiter-flexible": "rate_limit",
    "cache-manager-redis-store": "cache",
}
PYTHON_FRAMEWORKS = {
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
}
PYTHON_REDIS_DEPENDENCIES = {
    "redis": "client",
    "aioredis": "client",
    "django-redis": "cache",
    "celery": "queue",
    "rq": "queue",
    "dramatiq": "queue",
}
JAVA_FRAMEWORK_MARKERS = {
    "spring-boot-starter-web": "spring",
    "spring-boot-starter": "spring",
}
JAVA_REDIS_DEPENDENCIES = {
    "spring-boot-starter-data-redis": "client",
    "spring-session-data-redis": "session",
    "redisson": "client",
    "lettuce-core": "client",
}
GO_FRAMEWORK_MARKERS = {
    "github.com/gin-gonic/gin": "gin",
    "github.com/go-chi/chi": "chi",
    "github.com/gofiber/fiber": "fiber",
    "github.com/labstack/echo": "echo",
}
GO_REDIS_DEPENDENCIES = {
    "github.com/redis/go-redis/v9": "client",
    "github.com/gomodule/redigo": "client",
    "github.com/hibiken/asynq": "queue",
}
REDIS_CONFIG_FILES = {
    "application.properties",
    "application.yaml",
    "application.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "compose.yaml",
}
CLIENT_ROLES = {"client"}


@dataclass
class DependencySignal:
    name: str
    role: str
    source: str
    evidence: str


@dataclass
class ManifestSignal:
    path: str
    kind: str


@dataclass
class FileSignal:
    path: str
    evidence: str


@dataclass
class IntegrationCandidate:
    path: str
    line: int
    evidence: str
    priority: int


PATTERN_DEFINITIONS: dict[str, list[tuple[str, int]]] = {
    "cache": [
        (r"@EnableCaching", 100),
        (r"cacheManager", 95),
        (r"django\.core\.cache", 95),
        (r"RedisCache", 90),
        (r"Redis\.from_url", 90),
        (r"cache\.(get|set|delete)\(", 85),
    ],
    "session": [
        (r"express-session", 100),
        (r"connect-redis", 100),
        (r"\bsession\(", 90),
        (r"SessionMiddleware", 90),
        (r"spring\.session", 85),
        (r"store-type:\s*redis", 85),
    ],
    "queue": [
        (r"bullmq", 100),
        (r"\bbull\b", 96),
        (r"\bCelery\b", 95),
        (r"\bRQ\b", 90),
        (r"\basynq\b", 90),
        (r"\bQueue\(", 85),
        (r"queue\.add\(", 85),
    ],
    "rate_limit": [
        (r"rate.?limit", 100),
        (r"rate-limiter", 95),
        (r"\bLimiter\(", 90),
        (r"\bthrottle", 90),
        (r"\bslowapi\b", 88),
        (r"\bBucket4j\b", 88),
    ],
}
COMPILED_PATTERNS = {
    kind: [(re.compile(pattern, re.IGNORECASE), priority) for pattern, priority in items]
    for kind, items in PATTERN_DEFINITIONS.items()
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a repository for Redis-relevant dependencies and integration seams."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args(argv)


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def should_skip_part(part: str) -> bool:
    lowered = part.lower()
    return (
        lowered in SKIP_DIRS
        or lowered == "tmp"
        or lowered.startswith("_tmp")
        or lowered.startswith(".tmp")
        or lowered.startswith(".uv-")
    )


def normalize_dependency_name(raw_name: str) -> str:
    stripped = raw_name.strip().strip('"').strip("'")
    match = re.match(r"([A-Za-z0-9@._/-]+)", stripped)
    return match.group(1).lower() if match else stripped.lower()


def add_unique_string(target: list[str], value: str) -> None:
    if value not in target:
        target.append(value)


def add_dependency(
    target: dict[str, DependencySignal],
    name: str,
    role: str,
    source: str,
    evidence: str,
) -> None:
    key = name.lower()
    if key not in target:
        target[key] = DependencySignal(name=name, role=role, source=source, evidence=evidence)


def parse_package_json(root: Path, manifests: list[ManifestSignal], stacks: list[str], frameworks: list[str], dependencies: dict[str, DependencySignal]) -> None:
    package_json = root / "package.json"
    if not package_json.exists():
        return
    manifests.append(ManifestSignal(path=relative_to_root(package_json, root), kind="package.json"))
    add_unique_string(stacks, "node")

    data = json.loads(package_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return
    sections = ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
    all_dependencies: dict[str, str] = {}
    for section in sections:
        bucket = data.get(section)
        if isinstance(bucket, dict):
            for name, version in bucket.items():
                if isinstance(version, str):
                    all_dependencies[name] = version

    for package_name in all_dependencies:
        if package_name in NODE_FRAMEWORKS:
            add_unique_string(frameworks, NODE_FRAMEWORKS[package_name])
        if package_name in NODE_REDIS_DEPENDENCIES:
            add_dependency(
                dependencies,
                package_name,
                NODE_REDIS_DEPENDENCIES[package_name],
                "package.json",
                f"Dependency '{package_name}' declared in package.json.",
            )


def extract_pyproject_dependencies(data: dict[str, object]) -> list[str]:
    discovered: list[str] = []
    project = data.get("project")
    if isinstance(project, dict):
        deps = project.get("dependencies")
        if isinstance(deps, list):
            for item in deps:
                if isinstance(item, str):
                    discovered.append(normalize_dependency_name(item))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for group in optional.values():
                if isinstance(group, list):
                    for item in group:
                        if isinstance(item, str):
                            discovered.append(normalize_dependency_name(item))

    tool = data.get("tool")
    if isinstance(tool, dict):
        poetry = tool.get("poetry")
        if isinstance(poetry, dict):
            poetry_deps = poetry.get("dependencies")
            if isinstance(poetry_deps, dict):
                for name in poetry_deps:
                    if name.lower() != "python":
                        discovered.append(normalize_dependency_name(name))
    return discovered


def parse_pyproject(root: Path, manifests: list[ManifestSignal], stacks: list[str], frameworks: list[str], dependencies: dict[str, DependencySignal]) -> None:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return
    manifests.append(ManifestSignal(path=relative_to_root(pyproject, root), kind="pyproject.toml"))
    add_unique_string(stacks, "python")

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    for dependency_name in extract_pyproject_dependencies(data if isinstance(data, dict) else {}):
        if dependency_name in PYTHON_FRAMEWORKS:
            add_unique_string(frameworks, PYTHON_FRAMEWORKS[dependency_name])
        if dependency_name in PYTHON_REDIS_DEPENDENCIES:
            add_dependency(
                dependencies,
                dependency_name,
                PYTHON_REDIS_DEPENDENCIES[dependency_name],
                "pyproject.toml",
                f"Dependency '{dependency_name}' declared in pyproject.toml.",
            )


def extract_artifact_ids(text: str) -> list[str]:
    return re.findall(r"<artifactId>([^<]+)</artifactId>", text)


def parse_pom(root: Path, manifests: list[ManifestSignal], stacks: list[str], frameworks: list[str], dependencies: dict[str, DependencySignal]) -> None:
    pom_xml = root / "pom.xml"
    if not pom_xml.exists():
        return
    manifests.append(ManifestSignal(path=relative_to_root(pom_xml, root), kind="pom.xml"))
    add_unique_string(stacks, "java")

    content = pom_xml.read_text(encoding="utf-8")
    for artifact_id in extract_artifact_ids(content):
        marker = artifact_id.strip()
        if marker in JAVA_FRAMEWORK_MARKERS:
            add_unique_string(frameworks, JAVA_FRAMEWORK_MARKERS[marker])
        if marker in JAVA_REDIS_DEPENDENCIES:
            add_dependency(
                dependencies,
                marker,
                JAVA_REDIS_DEPENDENCIES[marker],
                "pom.xml",
                f"Artifact '{marker}' declared in pom.xml.",
            )


def parse_go_mod(root: Path, manifests: list[ManifestSignal], stacks: list[str], frameworks: list[str], dependencies: dict[str, DependencySignal]) -> None:
    go_mod = root / "go.mod"
    if not go_mod.exists():
        return
    manifests.append(ManifestSignal(path=relative_to_root(go_mod, root), kind="go.mod"))
    add_unique_string(stacks, "go")

    content = go_mod.read_text(encoding="utf-8")
    for module_name in re.findall(r"^\s*([A-Za-z0-9./_-]+)\s+v[0-9]", content, re.MULTILINE):
        if module_name in GO_FRAMEWORK_MARKERS:
            add_unique_string(frameworks, GO_FRAMEWORK_MARKERS[module_name])
        if module_name in GO_REDIS_DEPENDENCIES:
            add_dependency(
                dependencies,
                module_name,
                GO_REDIS_DEPENDENCIES[module_name],
                "go.mod",
                f"Module '{module_name}' declared in go.mod.",
            )


def iter_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(should_skip_part(part) for part in path.parts):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_SCAN_FILE_SIZE:
                continue
        except OSError:
            continue
        files.append(path)
    return files


def detect_config_files(root: Path) -> list[FileSignal]:
    signals: list[FileSignal] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(should_skip_part(part) for part in path.parts):
            continue
        name = path.name
        if not (name in REDIS_CONFIG_FILES or name.startswith(".env")):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lowered = content.lower()
        if "redis" not in lowered and "redis_" not in lowered:
            continue
        signals.append(
            FileSignal(
                path=relative_to_root(path, root),
                evidence=f"Redis configuration signal found in {name}.",
            )
        )
    return sorted(signals, key=lambda item: item.path)


def scan_integration_candidates(root: Path) -> dict[str, list[IntegrationCandidate]]:
    buckets: dict[str, dict[str, IntegrationCandidate]] = {
        "cache": {},
        "session": {},
        "queue": {},
        "rate_limit": {},
    }
    for path in iter_candidate_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        relative_path = relative_to_root(path, root)
        for line_number, line in enumerate(lines, start=1):
            for kind, patterns in COMPILED_PATTERNS.items():
                for pattern, priority in patterns:
                    if not pattern.search(line):
                        continue
                    current = buckets[kind].get(relative_path)
                    candidate = IntegrationCandidate(
                        path=relative_path,
                        line=line_number,
                        evidence=line.strip(),
                        priority=priority,
                    )
                    if current is None or candidate.priority > current.priority:
                        buckets[kind][relative_path] = candidate
                    break
    return {
        kind: sorted(
            (asdict(candidate) for candidate in bucket.values()),
            key=lambda item: (-int(item["priority"]), str(item["path"])),
        )
        for kind, bucket in buckets.items()
        if bucket
    }


def build_recommendations(
    frameworks: list[str],
    redis_dependencies: list[DependencySignal],
    config_files: list[FileSignal],
    integration_candidates: dict[str, list[dict[str, object]]],
) -> list[str]:
    recommendations: list[str] = []
    roles = {item.role for item in redis_dependencies}
    dependency_names = {item.name for item in redis_dependencies}

    if not roles.intersection(CLIENT_ROLES):
        recommendations.append(
            "Add one dedicated Redis client that matches the detected stack before wiring higher-level adapters."
        )
    if integration_candidates.get("session"):
        recommendations.append(
            "Prefer adapting the existing session/auth seam with a Redis-backed store instead of replacing the whole session stack."
        )
    if integration_candidates.get("queue") and dependency_names.intersection({"bull", "bullmq", "celery", "rq", "github.com/hibiken/asynq"}):
        recommendations.append(
            "Reuse the queue library's existing Redis connection seam rather than creating raw clients inside handlers or workers."
        )
    if integration_candidates.get("cache"):
        recommendations.append(
            "Prefer the framework cache abstraction or a dedicated cache service seam instead of scattering direct Redis calls across handlers."
        )
    if "spring" in frameworks and "spring-session-data-redis" in dependency_names:
        recommendations.append(
            "Keep Spring Session on the existing HttpSession seam and configure Redis through spring.session and spring.data.redis properties."
        )
    if not config_files:
        recommendations.append(
            "Introduce explicit REDIS_URL or equivalent config wiring before touching runtime code."
        )
    return recommendations


def build_risks(
    redis_dependencies: list[DependencySignal],
    config_files: list[FileSignal],
    integration_candidates: dict[str, list[dict[str, object]]],
) -> list[str]:
    risks: list[str] = []
    client_dependencies = [item.name for item in redis_dependencies if item.role in CLIENT_ROLES]
    if len(client_dependencies) > 1:
        risks.append(
            "Multiple Redis client packages detected; verify whether the project should standardize on one connection layer."
        )
    if not config_files:
        risks.append("No Redis configuration signal detected; plan env/config wiring before code changes.")
    if not integration_candidates:
        risks.append("No obvious cache, session, queue, or rate-limit seams were detected; inspect entrypoints manually.")
    return risks


def inspect_repository(root: Path) -> dict[str, object]:
    manifests: list[ManifestSignal] = []
    stacks: list[str] = []
    frameworks: list[str] = []
    dependency_map: dict[str, DependencySignal] = {}

    parse_package_json(root, manifests, stacks, frameworks, dependency_map)
    parse_pyproject(root, manifests, stacks, frameworks, dependency_map)
    parse_pom(root, manifests, stacks, frameworks, dependency_map)
    parse_go_mod(root, manifests, stacks, frameworks, dependency_map)

    redis_dependencies = sorted(dependency_map.values(), key=lambda item: (item.role, item.name))
    config_files = detect_config_files(root)
    integration_candidates = scan_integration_candidates(root)
    risks = build_risks(redis_dependencies, config_files, integration_candidates)
    recommendations = build_recommendations(frameworks, redis_dependencies, config_files, integration_candidates)

    return {
        "project_root": str(root),
        "stacks": stacks,
        "frameworks": frameworks,
        "manifests": [asdict(item) for item in manifests],
        "redis_dependencies": [asdict(item) for item in redis_dependencies],
        "config_files": [asdict(item) for item in config_files],
        "integration_candidates": integration_candidates,
        "risks": risks,
        "recommendations": recommendations,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    payload = inspect_repository(root)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Project root: {payload['project_root']}")
        print(f"Stacks: {', '.join(payload['stacks']) or 'none'}")
        print(f"Frameworks: {', '.join(payload['frameworks']) or 'none'}")
        print("Redis dependencies:")
        for item in payload["redis_dependencies"]:
            print(f"  - {item['name']} ({item['role']}) [{item['source']}]")
        print("Integration candidates:")
        for kind, items in payload["integration_candidates"].items():
            print(f"  {kind}:")
            for item in items:
                print(f"    - {item['path']}:{item['line']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
