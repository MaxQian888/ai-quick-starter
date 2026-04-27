#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote


DEFAULT_API_BASE_URL = "https://api.github.com"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-actions-ci-builder",
}
UNSTABLE_TAG_MARKERS = ("alpha", "beta", "rc", "preview", "canary", "nightly")


@dataclass(frozen=True)
class ComponentCatalogEntry:
    repo: str
    category: str
    summary: str
    keywords: tuple[str, ...]
    official: bool
    docs_url: str


@dataclass(frozen=True)
class LatestReference:
    repo: str
    tag: str
    commit_sha: str
    release_url: str
    published_at: str
    source_kind: str
    immutable: bool
    pin_hint: str


@dataclass(frozen=True)
class WorkflowActionReference:
    raw: str
    kind: str
    repo: str | None
    current_ref: str
    line_number: int


@dataclass(frozen=True)
class WorkflowActionStatus:
    raw: str
    kind: str
    repo: str | None
    current_ref: str
    status: str
    line_number: int
    latest_tag: str | None = None
    latest_commit_sha: str | None = None
    release_url: str | None = None
    pin_hint: str | None = None
    published_at: str | None = None
    immutable_release: bool | None = None
    verification_error: str | None = None


@dataclass(frozen=True)
class WorkflowStep:
    kind: str
    value: str
    name: str = ""


@dataclass(frozen=True)
class WorkflowJob:
    job_id: str
    name: str
    steps: tuple[WorkflowStep, ...]


class GitHubApiError(RuntimeError):
    pass


COMMON_COMPONENTS = (
    ComponentCatalogEntry("actions/checkout", "core", "Check out repository contents onto the runner.", ("checkout", "clone", "source", "git", "repository"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("actions/cache", "performance", "Restore and save dependency or build caches.", ("cache", "dependency", "performance", "restore", "save"), True, "https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows"),
    ComponentCatalogEntry("actions/setup-node", "node", "Install Node.js and optionally enable npm, pnpm, or yarn caching.", ("node", "npm", "pnpm", "yarn", "javascript", "typescript"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("pnpm/action-setup", "node", "Install pnpm for Node.js CI pipelines.", ("pnpm", "node", "javascript", "typescript", "package-manager"), False, "https://github.com/pnpm/action-setup"),
    ComponentCatalogEntry("actions/setup-python", "python", "Install Python and support pip caching for CI jobs.", ("python", "pip", "pytest", "ruff", "poetry", "uv"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("astral-sh/setup-uv", "python", "Install uv and enable modern Python dependency workflows.", ("python", "uv", "astral", "pip", "lockfile"), False, "https://github.com/astral-sh/setup-uv"),
    ComponentCatalogEntry("actions/setup-go", "go", "Install Go and configure module caching.", ("go", "golang", "go test", "modules"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("actions/setup-java", "java", "Install Java and enable Gradle or Maven caching.", ("java", "gradle", "maven", "jdk"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("actions/setup-dotnet", "dotnet", "Install .NET SDKs for build and test jobs.", ("dotnet", "csharp", "nuget", ".net"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("actions/upload-artifact", "artifacts", "Upload workflow artifacts such as reports, logs, or coverage files.", ("artifact", "upload", "report", "coverage", "logs"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("actions/download-artifact", "artifacts", "Download artifacts from previous jobs or reusable workflows.", ("artifact", "download", "report", "coverage", "logs"), True, "https://docs.github.com/en/actions"),
    ComponentCatalogEntry("docker/setup-buildx-action", "docker", "Provision Docker Buildx for image builds.", ("docker", "buildx", "container", "image"), False, "https://github.com/docker/setup-buildx-action"),
    ComponentCatalogEntry("docker/login-action", "docker", "Authenticate to Docker registries before build or push steps.", ("docker", "registry", "login", "container", "push"), False, "https://github.com/docker/login-action"),
    ComponentCatalogEntry("docker/build-push-action", "docker", "Build and optionally push Docker images with BuildKit.", ("docker", "build", "push", "container", "image"), False, "https://github.com/docker/build-push-action"),
    ComponentCatalogEntry("github/codeql-action", "security", "Run CodeQL code scanning in GitHub Actions.", ("codeql", "security", "scan", "analysis", "code-scanning"), False, "https://github.com/github/codeql-action"),
)


class GitHubApiClient:
    def __init__(self, base_url: str = DEFAULT_API_BASE_URL, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def get_json(self, path: str) -> object:
        headers = dict(DEFAULT_HEADERS)
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(f"{self.base_url}{path}", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 403 and "rate limit" in body.lower():
                raise GitHubApiError(
                    "GitHub API rate limit exceeded. Set GITHUB_TOKEN or GH_TOKEN, or narrow the query and retry."
                ) from exc
            raise GitHubApiError(f"{exc.code} {exc.reason}: {body}") from exc
        except urllib.error.URLError as exc:
            raise GitHubApiError(f"Network error while requesting {path}: {exc.reason}") from exc


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9./-]+", text.lower())


def repo_looks_direct(text: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", text.strip().lower()))


def catalog_entry_for_repo(repo: str) -> ComponentCatalogEntry:
    for entry in COMMON_COMPONENTS:
        if entry.repo == repo:
            return entry
    return ComponentCatalogEntry(repo, "custom", "Resolve the latest stable reference for a custom GitHub Actions component.", tuple(tokenize(repo)), False, f"https://github.com/{repo}")


def discover_components(query: str, limit: int = 8, catalog: Iterable[ComponentCatalogEntry] = COMMON_COMPONENTS) -> list[ComponentCatalogEntry]:
    tokens = tokenize(query)
    if not tokens:
        return []
    direct_repo = query.strip().lower() if repo_looks_direct(query) else None
    scored: list[tuple[int, ComponentCatalogEntry]] = []
    for entry in catalog:
        haystack = set(tokenize(" ".join((entry.repo, entry.category, entry.summary, *entry.keywords))))
        score = sum(3 for token in tokens if token in haystack)
        if direct_repo and direct_repo == entry.repo:
            score += 100
        elif direct_repo and direct_repo in entry.repo:
            score += 50
        if score:
            scored.append((score, entry))
    if not scored and direct_repo:
        return [catalog_entry_for_repo(direct_repo)]
    scored.sort(key=lambda item: (-item[0], item[1].repo))
    return [entry for _, entry in scored[:limit]]


def is_stable_tag(tag: str) -> bool:
    lowered = tag.lower()
    return not any(marker in lowered for marker in UNSTABLE_TAG_MARKERS)


def resolve_tag_commit_sha(repo: str, tag: str, client: GitHubApiClient | None = None) -> str:
    api_client = client or GitHubApiClient()
    ref = api_client.get_json(f"/repos/{repo}/git/ref/tags/{quote(tag, safe='')}")
    if not isinstance(ref, dict):
        raise GitHubApiError(f"Unexpected git ref response for {repo}@{tag}")
    obj = ref.get("object", {})
    obj_type = obj.get("type")
    obj_sha = obj.get("sha")
    if not isinstance(obj_sha, str):
        raise GitHubApiError(f"Missing object SHA for {repo}@{tag}")
    if obj_type == "commit":
        return obj_sha
    if obj_type == "tag":
        annotated = api_client.get_json(f"/repos/{repo}/git/tags/{obj_sha}")
        if not isinstance(annotated, dict):
            raise GitHubApiError(f"Unexpected annotated tag response for {repo}@{tag}")
        target_sha = annotated.get("object", {}).get("sha")
        if not isinstance(target_sha, str):
            raise GitHubApiError(f"Missing commit SHA in annotated tag for {repo}@{tag}")
        return target_sha
    raise GitHubApiError(f"Unsupported git object type for {repo}@{tag}: {obj_type}")


def resolve_latest_reference(repo: str, client: GitHubApiClient | None = None) -> LatestReference:
    api_client = client or GitHubApiClient()
    tag = ""
    release_url = f"https://github.com/{repo}/tags"
    published_at = ""
    source_kind = "tag"
    immutable = False
    try:
        release = api_client.get_json(f"/repos/{repo}/releases/latest")
        if not isinstance(release, dict):
            raise GitHubApiError(f"Unexpected latest release response for {repo}")
        tag = str(release.get("tag_name", "")).strip()
        release_url = str(release.get("html_url", release_url))
        published_at = str(release.get("published_at", "")).strip()
        source_kind = "release"
        immutable = bool(release.get("immutable", False))
    except GitHubApiError as exc:
        if "404" not in str(exc):
            raise
    if not tag:
        tags = api_client.get_json(f"/repos/{repo}/tags?per_page=20")
        if not isinstance(tags, list) or not tags:
            raise GitHubApiError(f"No tags found for {repo}")
        chosen = next((item for item in tags if is_stable_tag(str(item.get('name', '')))), tags[0])
        tag = str(chosen.get("name", "")).strip()
        release_url = f"https://github.com/{repo}/tree/{tag}"
    if not tag:
        raise GitHubApiError(f"Latest tag could not be determined for {repo}")
    commit_sha = resolve_tag_commit_sha(repo, tag, client=api_client)
    return LatestReference(repo, tag, commit_sha, release_url, published_at, source_kind, immutable, f"{repo}@{commit_sha} # {tag}")


def looks_like_sha(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{40}", value.lower()))


def looks_like_floating_ref(value: str) -> bool:
    lowered = value.lower()
    return lowered in {"main", "master", "latest"} or bool(re.fullmatch(r"v\d+", lowered)) or bool(re.fullmatch(r"v\d+\.\d+", lowered))


def classify_ref_status(current_ref: str, latest: LatestReference) -> str:
    if not current_ref:
        return "missing-ref"
    if looks_like_sha(current_ref):
        return "up-to-date" if current_ref.lower() == latest.commit_sha.lower() else "outdated"
    if current_ref == latest.tag:
        return "up-to-date"
    if looks_like_floating_ref(current_ref):
        if current_ref.startswith("v") and latest.tag.startswith("v"):
            current_major = current_ref.split(".", 1)[0]
            latest_major = latest.tag.split(".", 1)[0]
            return "floating-ref" if current_major == latest_major else "outdated"
        return "floating-ref"
    return "outdated"


def parse_uses_target(value: str, line_number: int) -> WorkflowActionReference:
    raw = value.strip()
    if raw.startswith("./"):
        kind = "local-reusable-workflow" if ".github/workflows/" in raw else "local-action"
        return WorkflowActionReference(raw, kind, None, raw, line_number)
    repo_part, _, ref = raw.partition("@")
    if "/.github/workflows/" in repo_part:
        return WorkflowActionReference(raw, "remote-reusable-workflow", repo_part, ref, line_number)
    return WorkflowActionReference(raw, "remote-action", repo_part, ref, line_number)


def extract_action_references(workflow_text: str) -> list[WorkflowActionReference]:
    pattern = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)")
    references: list[WorkflowActionReference] = []
    for line_number, raw_line in enumerate(workflow_text.splitlines(), start=1):
        match = pattern.match(raw_line)
        if match:
            references.append(parse_uses_target(match.group(1), line_number))
    return references


def scan_workflow_actions(workflow_text: str, client: GitHubApiClient | None = None) -> list[WorkflowActionStatus]:
    api_client = client or GitHubApiClient()
    cache: dict[str, LatestReference] = {}
    results: list[WorkflowActionStatus] = []
    for reference in extract_action_references(workflow_text):
        if reference.kind in {"local-action", "local-reusable-workflow", "remote-reusable-workflow"}:
            results.append(WorkflowActionStatus(reference.raw, reference.kind, reference.repo, reference.current_ref, reference.kind, reference.line_number))
            continue
        repo = reference.repo or ""
        try:
            if repo not in cache:
                cache[repo] = resolve_latest_reference(repo, client=api_client)
            latest = cache[repo]
        except GitHubApiError as exc:
            results.append(
                WorkflowActionStatus(
                    reference.raw,
                    reference.kind,
                    repo,
                    reference.current_ref,
                    "verification-blocked",
                    reference.line_number,
                    verification_error=str(exc),
                )
            )
            continue
        results.append(
            WorkflowActionStatus(
                reference.raw,
                reference.kind,
                repo,
                reference.current_ref,
                classify_ref_status(reference.current_ref, latest),
                reference.line_number,
                latest.tag,
                latest.commit_sha,
                latest.release_url,
                latest.pin_hint,
                latest.published_at,
                latest.immutable,
                None,
            )
        )
    return results


def serialize_latest_reference(entry: ComponentCatalogEntry, latest: LatestReference) -> dict[str, object]:
    return {
        "repo": entry.repo,
        "category": entry.category,
        "summary": entry.summary,
        "official": entry.official,
        "docs_url": entry.docs_url,
        "latest_tag": latest.tag,
        "latest_commit_sha": latest.commit_sha,
        "release_url": latest.release_url,
        "published_at": latest.published_at,
        "source_kind": latest.source_kind,
        "immutable_release": latest.immutable,
        "pin_hint": latest.pin_hint,
    }


def build_component_payload(repos: Iterable[str] | None = None, query: str | None = None, limit: int = 4, client: GitHubApiClient | None = None) -> dict[str, object]:
    api_client = client or GitHubApiClient()
    selected: list[ComponentCatalogEntry] = []
    if query:
        selected.extend(discover_components(query, limit=limit))
    if repos:
        for repo in repos:
            entry = catalog_entry_for_repo(repo)
            if all(existing.repo != entry.repo for existing in selected):
                selected.append(entry)
    payload = {"components": []}
    for entry in selected:
        latest = resolve_latest_reference(entry.repo, client=api_client)
        payload["components"].append(serialize_latest_reference(entry, latest))
    return payload


def parse_scalar_value(stripped: str) -> str:
    value = stripped.split(":", 1)[1].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_workflow_triggers(workflow_text: str) -> list[str]:
    triggers: list[str] = []
    in_on_block = False
    on_indent = 0
    for raw_line in workflow_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0 and stripped.startswith("on:"):
            rest = stripped[3:].strip()
            if rest.startswith("[") and rest.endswith("]"):
                triggers.extend(item.strip(" '\"") for item in rest[1:-1].split(",") if item.strip())
                in_on_block = False
            elif rest:
                triggers.append(rest.strip(" '\""))
                in_on_block = False
            else:
                in_on_block = True
                on_indent = indent
            continue
        if in_on_block:
            if indent <= on_indent:
                break
            if indent == 2:
                event = stripped.split(":", 1)[0].strip()
                if event and event not in triggers:
                    triggers.append(event)
    return triggers


def parse_workflow_jobs(workflow_text: str) -> list[WorkflowJob]:
    jobs: list[WorkflowJob] = []
    current_job_id = ""
    current_job_name = ""
    current_steps: list[WorkflowStep] = []
    current_step_kind = ""
    current_step_value = ""
    current_step_name = ""
    in_jobs = False
    in_steps = False

    def finalize_step() -> None:
        nonlocal current_step_kind, current_step_value, current_step_name
        if current_step_kind and current_step_value:
            current_steps.append(WorkflowStep(current_step_kind, current_step_value, current_step_name))
        current_step_kind = ""
        current_step_value = ""
        current_step_name = ""

    def finalize_job() -> None:
        nonlocal current_job_id, current_job_name, current_steps
        finalize_step()
        if current_job_id:
            jobs.append(WorkflowJob(current_job_id, current_job_name or current_job_id, tuple(current_steps)))
        current_job_id = ""
        current_job_name = ""
        current_steps = []

    for raw_line in workflow_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0 and stripped == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        if indent == 2 and stripped.endswith(":") and not stripped.startswith(("name:", "env:", "defaults:")):
            finalize_job()
            current_job_id = stripped[:-1]
            in_steps = False
            continue
        if not current_job_id:
            continue
        if indent == 4 and stripped.startswith("name:"):
            current_job_name = parse_scalar_value(stripped)
            continue
        if indent == 4 and stripped == "steps:":
            in_steps = True
            continue
        if not in_steps:
            continue
        if indent == 6 and stripped.startswith("- "):
            finalize_step()
            stripped = stripped[2:].strip()
            if stripped.startswith("uses:"):
                current_step_kind = "uses"
                current_step_value = parse_scalar_value(stripped)
            elif stripped.startswith("run:"):
                current_step_kind = "run"
                current_step_value = parse_scalar_value(stripped)
            elif stripped.startswith("name:"):
                current_step_name = parse_scalar_value(stripped)
            continue
        if indent >= 8:
            if stripped.startswith("uses:"):
                current_step_kind = "uses"
                current_step_value = parse_scalar_value(stripped)
            elif stripped.startswith("run:"):
                current_step_kind = "run"
                current_step_value = parse_scalar_value(stripped)
            elif stripped.startswith("name:"):
                current_step_name = parse_scalar_value(stripped)
            continue
        if indent <= 4:
            finalize_step()
            in_steps = False

    finalize_job()
    return jobs


def classify_job_kind(job: WorkflowJob) -> str:
    text = " ".join([job.job_id, job.name, *[step.value for step in job.steps if step.kind in {"run", "uses"}]]).lower()
    if any(keyword in text for keyword in ("release", "publish", "deploy", "docker push", "gh release")):
        return "release"
    if any(keyword in text for keyword in ("codeql", "security", "scan", "scorecards")):
        return "security"
    return "validation"


def is_support_use(value: str) -> bool:
    repo = value.partition("@")[0]
    return repo in {
        "actions/checkout",
        "actions/cache",
        "actions/setup-node",
        "actions/setup-python",
        "actions/setup-go",
        "actions/setup-java",
        "actions/setup-dotnet",
        "pnpm/action-setup",
        "astral-sh/setup-uv",
        "docker/setup-buildx-action",
        "docker/login-action",
    }


def is_install_command(value: str) -> bool:
    lowered = value.lower()
    markers = (
        "pnpm install",
        "pnpm fetch",
        "npm ci",
        "npm install",
        "yarn install",
        "pip install",
        "uv sync",
        "go mod download",
        "mvn -b",
        "mvn --batch-mode",
        "gradle dependencies",
        "dotnet restore",
    )
    return any(marker in lowered for marker in markers)


def normalize_setup_step(step: WorkflowStep) -> str:
    if step.kind == "uses":
        return f"uses:{step.value.partition('@')[0]}"
    normalized = re.sub(r"\s+", " ", step.value.strip().lower())
    return f"run:{normalized}"


def detect_repeated_setup_prefixes(jobs: Iterable[WorkflowJob]) -> list[dict[str, object]]:
    groups: dict[tuple[str, ...], list[str]] = {}
    for job in jobs:
        prefix: list[str] = []
        for step in job.steps:
            if step.kind == "uses" and is_support_use(step.value):
                prefix.append(normalize_setup_step(step))
                continue
            if step.kind == "run" and is_install_command(step.value):
                prefix.append(normalize_setup_step(step))
                continue
            break
        if len(prefix) < 2:
            continue
        groups.setdefault(tuple(prefix), []).append(job.job_id)

    matches: list[dict[str, object]] = []
    for prefix, job_ids in groups.items():
        if len(job_ids) >= 2:
            matches.append({"signature": list(prefix), "jobs": sorted(job_ids)})
    matches.sort(key=lambda item: (-len(item["jobs"]), -len(item["signature"])))
    return matches


def infer_stack_slug(signature: Iterable[str]) -> str:
    joined = " ".join(signature)
    if "actions/setup-node" in joined and "pnpm/action-setup" in joined:
        return "node-pnpm"
    if "actions/setup-node" in joined:
        return "node"
    if "actions/setup-python" in joined or "astral-sh/setup-uv" in joined:
        return "python"
    if "actions/setup-go" in joined:
        return "go"
    if "actions/setup-java" in joined:
        return "java"
    if "actions/setup-dotnet" in joined:
        return "dotnet"
    if "docker/setup-buildx-action" in joined:
        return "docker"
    return "shared"


def build_split_plan(workflow_text: str, workflow_name: str) -> dict[str, object]:
    triggers = parse_workflow_triggers(workflow_text)
    jobs = parse_workflow_jobs(workflow_text)
    repeated_prefixes = detect_repeated_setup_prefixes(jobs)
    line_count = len(workflow_text.splitlines())
    recommendations: list[dict[str, object]] = []
    target_files: list[dict[str, object]] = []

    validation_jobs = [job for job in jobs if classify_job_kind(job) == "validation"]
    release_jobs = [job for job in jobs if classify_job_kind(job) == "release"]

    if validation_jobs and release_jobs:
        recommendations.append({"kind": "split-by-lifecycle", "reason": "Validation and release work live in the same workflow file."})
        target_files.append({"path": ".github/workflows/ci.yml", "role": "entrypoint-workflow", "jobs": [job.job_id for job in validation_jobs], "reason": "Keep pull_request and push validation isolated from publishing or deployment."})
        target_files.append({"path": ".github/workflows/release.yml", "role": "entrypoint-workflow", "jobs": [job.job_id for job in release_jobs], "reason": "Keep release, publish, or deploy automation on an isolated trigger path."})

    if "schedule" in triggers and len(triggers) > 1:
        recommendations.append({"kind": "split-by-trigger", "reason": "Scheduled execution is mixed with interactive or PR validation triggers."})
        target_files.append({"path": ".github/workflows/nightly.yml", "role": "entrypoint-workflow", "jobs": [job.job_id for job in jobs], "reason": "Separate scheduled automation from PR and branch feedback loops."})

    if repeated_prefixes:
        strongest = repeated_prefixes[0]
        stack_slug = infer_stack_slug(strongest["signature"])
        reusable_stack_slug = stack_slug.split("-", 1)[0] if stack_slug.startswith("node-") else stack_slug
        recommendations.append({"kind": "extract-composite-action", "reason": "Multiple jobs repeat the same setup and install sequence.", "jobs": strongest["jobs"]})
        target_files.append({"path": f".github/actions/{stack_slug}-bootstrap/action.yml", "role": "composite-action", "jobs": strongest["jobs"], "reason": "Deduplicate shared runner bootstrap steps."})
        if len(validation_jobs) >= 2:
            recommendations.append({"kind": "extract-reusable-workflow", "reason": "Validation jobs share one repeated structure and are good candidates for workflow_call reuse.", "jobs": strongest["jobs"]})
            target_files.append({"path": f".github/workflows/reusable-{reusable_stack_slug}-quality.yml", "role": "reusable-workflow", "jobs": strongest["jobs"], "reason": "Move repeated quality gates into a reusable workflow rooted in .github/workflows."})

    oversized = line_count >= 160 or len(jobs) >= 5 or len(triggers) >= 4
    if oversized and not recommendations:
        recommendations.append({"kind": "split-by-size", "reason": "The workflow is large enough that entrypoint and reusable files should be separated."})

    return {
        "workflow_name": workflow_name,
        "line_count": line_count,
        "triggers": triggers,
        "job_count": len(jobs),
        "jobs": [job.job_id for job in jobs],
        "oversized": oversized,
        "recommendations": recommendations,
        "target_files": target_files,
        "repeated_setup_blocks": repeated_prefixes,
    }


def workflow_plan_payload(workflow_path: Path) -> dict[str, object]:
    return build_split_plan(workflow_path.read_text(encoding="utf-8"), workflow_path.name)


def workflow_status_payload(workflow_path: Path, client: GitHubApiClient | None = None) -> dict[str, object]:
    items = scan_workflow_actions(workflow_path.read_text(encoding="utf-8"), client=client)
    return {"workflow": str(workflow_path), "items": [asdict(item) for item in items]}


SUPPORTED_ACT_USES_PREFIXES = (
    "actions/checkout@",
    "actions/setup-",
    "actions/cache@",
    "pnpm/action-setup@",
    "ruby/setup-ruby@",
    "actions/upload-artifact@",
    "actions/download-artifact@",
    "docker/setup-buildx-action@",
    "docker/login-action@",
    "docker/build-push-action@",
    "astral-sh/setup-uv@",
    "github/codeql-action/",
)

VALIDATION_KEYWORDS = (
    "test",
    "pytest",
    "unittest",
    "lint",
    "ruff",
    "mypy",
    "pyright",
    "typecheck",
    "check",
    "verify",
    "build",
    "compile",
)

DEPLOY_KEYWORDS = (
    "deploy",
    "release",
    "publish",
    "ship",
    "docker push",
)


@dataclass(frozen=True)
class LocalCiWorkflow:
    path: str
    name: str
    triggers: tuple[str, ...]
    jobs: tuple[WorkflowJob, ...]
    text: str


@dataclass(frozen=True)
class WorkflowInventoryRecord:
    path: str
    name: str
    triggers: tuple[str, ...]
    job_ids: tuple[str, ...]
    major_uses: tuple[str, ...]
    major_runs: tuple[str, ...]
    responsibility: str


@dataclass(frozen=True)
class GovernanceFinding:
    severity: str
    category: str
    evidence: str
    rationale: str
    recommended_fix: str


@dataclass(frozen=True)
class PerformanceRecommendation:
    kind: str
    current_pattern: str
    issue: str
    proposed_change: str
    expected_tradeoff: str


@dataclass(frozen=True)
class RepairQueueItem:
    kind: str
    reason: str
    evidence: tuple[str, ...]


REPAIR_QUEUE_ORDER = (
    "workflow-structure",
    "action-versioning",
    "permissions-and-governance",
    "environment-and-tooling",
    "repository-quality-gates",
    "product-code-failures",
)


def path_to_posix(path: Path) -> str:
    return path.as_posix()


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path_to_posix(path)


def tool_exists(name: str) -> bool:
    return shutil.which(name) is not None


def inspect_local_ci_environment() -> dict[str, bool]:
    return {
        "act": tool_exists("act"),
        "docker": tool_exists("docker"),
        "git": tool_exists("git"),
    }


def has_keyword(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def is_supported_act_use(value: str) -> bool:
    lowered = value.lower()
    return any(lowered.startswith(prefix) for prefix in SUPPORTED_ACT_USES_PREFIXES)


def discover_local_ci_workflows(root: Path) -> list[LocalCiWorkflow]:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return []

    workflows: list[LocalCiWorkflow] = []
    for workflow_path in sorted(workflow_dir.glob("*.y*ml")):
        text = workflow_path.read_text(encoding="utf-8")
        name = workflow_path.stem
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("name:"):
                name = parse_scalar_value(stripped)
                break
        workflows.append(
            LocalCiWorkflow(
                path=relative_to_root(workflow_path, root),
                name=name,
                triggers=tuple(parse_workflow_triggers(text)),
                jobs=tuple(parse_workflow_jobs(text)),
                text=text,
            )
        )
    return workflows


def job_signature(job: WorkflowJob) -> tuple[str, ...]:
    signature: list[str] = []
    for step in job.steps:
        if step.kind == "uses":
            signature.append(f"uses:{step.value.partition('@')[0]}")
        elif step.kind == "run":
            normalized = re.sub(r"\s+", " ", step.value.strip().lower())
            signature.append(f"run:{normalized}")
    return tuple(signature)


def classify_workflow_responsibility(workflow: LocalCiWorkflow) -> str:
    trigger_set = set(workflow.triggers)
    job_kinds = {classify_job_kind(job) for job in workflow.jobs}
    text = " ".join(
        [
            workflow.name,
            *workflow.triggers,
            *[job.job_id for job in workflow.jobs],
            *[job.name for job in workflow.jobs],
            *[step.value for job in workflow.jobs for step in job.steps],
        ]
    )
    if has_keyword(text, DEPLOY_KEYWORDS):
        return "mixed" if "validation" in job_kinds or len(trigger_set) > 1 else "deploy"
    if "release" in job_kinds:
        return "mixed" if "validation" in job_kinds or len(trigger_set) > 1 else "release"
    if "schedule" in trigger_set:
        return "nightly" if trigger_set == {"schedule"} else "mixed"
    return "validation"


def build_workflow_inventory(workflows: list[LocalCiWorkflow]) -> list[WorkflowInventoryRecord]:
    records: list[WorkflowInventoryRecord] = []
    for workflow in workflows:
        uses: list[str] = []
        runs: list[str] = []
        for job in workflow.jobs:
            for step in job.steps:
                if step.kind == "uses" and step.value not in uses:
                    uses.append(step.value)
                elif step.kind == "run" and step.value not in runs:
                    runs.append(step.value)
        records.append(
            WorkflowInventoryRecord(
                path=workflow.path,
                name=workflow.name,
                triggers=workflow.triggers,
                job_ids=tuple(job.job_id for job in workflow.jobs),
                major_uses=tuple(uses[:8]),
                major_runs=tuple(runs[:8]),
                responsibility=classify_workflow_responsibility(workflow),
            )
        )
    records.sort(key=lambda item: item.path)
    return records


def workflow_has_permissions(workflow: LocalCiWorkflow) -> bool:
    return bool(re.search(r"(?m)^\s*permissions\s*:", workflow.text))


def workflow_has_concurrency(workflow: LocalCiWorkflow) -> bool:
    return bool(re.search(r"(?m)^\s*concurrency\s*:", workflow.text))


def dependabot_has_actions_updates(root: Path) -> bool:
    dependabot_path = root / ".github" / "dependabot.yml"
    if not dependabot_path.exists():
        return False
    text = dependabot_path.read_text(encoding="utf-8")
    return 'package-ecosystem: "github-actions"' in text or "package-ecosystem: 'github-actions'" in text or "package-ecosystem: github-actions" in text


def detect_governance_findings(root: Path, workflows: list[LocalCiWorkflow]) -> list[GovernanceFinding]:
    findings: list[GovernanceFinding] = []
    for workflow in workflows:
        if not workflow_has_permissions(workflow):
            findings.append(
                GovernanceFinding(
                    severity="medium",
                    category="missing-permissions",
                    evidence=workflow.path,
                    rationale="Workflow does not declare explicit permissions, so the token scope is implicit.",
                    recommended_fix="Add explicit least-privilege permissions at workflow or job level.",
                )
            )
        if any(trigger in workflow.triggers for trigger in ("pull_request", "push")) and not workflow_has_concurrency(workflow):
            findings.append(
                GovernanceFinding(
                    severity="medium",
                    category="missing-concurrency",
                    evidence=workflow.path,
                    rationale="Branch-feedback workflows should cancel stale runs to reduce overlap and noisy feedback.",
                    recommended_fix="Add workflow-level concurrency with cancel-in-progress for PR or push validation.",
                )
            )
        for reference in extract_action_references(workflow.text):
            if reference.kind != "remote-action":
                continue
            if not looks_like_sha(reference.current_ref):
                findings.append(
                    GovernanceFinding(
                        severity="medium",
                        category="floating-ref",
                        evidence=f"{workflow.path}:{reference.line_number}:{reference.raw}",
                        rationale="Remote actions are not pinned to an immutable commit SHA.",
                        recommended_fix="Resolve the latest stable release and pin the action to its commit SHA.",
                    )
                )
    if not dependabot_has_actions_updates(root):
        findings.append(
            GovernanceFinding(
                severity="low",
                category="missing-actions-dependabot",
                evidence=str(root / ".github" / "dependabot.yml"),
                rationale="GitHub Actions refs will drift unless workflow dependencies are reviewed regularly.",
                recommended_fix="Add a GitHub Actions Dependabot update entry under .github/dependabot.yml.",
            )
        )
    return findings


def root_has_lockfile(root: Path) -> bool:
    lockfiles = (
        "pnpm-lock.yaml",
        "package-lock.json",
        "yarn.lock",
        "uv.lock",
        "poetry.lock",
        "go.sum",
        "Cargo.lock",
    )
    return any((root / name).exists() for name in lockfiles)


def workflow_has_cache_signal(workflow: LocalCiWorkflow) -> bool:
    if "actions/cache@" in workflow.text:
        return True
    return bool(re.search(r"(?m)^\s*cache\s*:", workflow.text))


def detect_performance_recommendations(root: Path, workflows: list[LocalCiWorkflow]) -> list[PerformanceRecommendation]:
    recommendations: list[PerformanceRecommendation] = []
    validation_jobs = [
        (workflow, job)
        for workflow in workflows
        for job in workflow.jobs
        if classify_job_kind(job) == "validation"
    ]

    signature_groups: dict[tuple[str, ...], list[str]] = {}
    for _, job in validation_jobs:
        signature = job_signature(job)
        if signature:
            signature_groups.setdefault(signature, []).append(job.job_id)
    if any(len(job_ids) >= 2 for job_ids in signature_groups.values()):
        repeated_jobs = max(signature_groups.values(), key=len)
        recommendations.append(
            PerformanceRecommendation(
                kind="use-matrix",
                current_pattern=", ".join(sorted(repeated_jobs)),
                issue="Multiple validation jobs repeat the same step sequence instead of varying through a matrix.",
                proposed_change="Replace duplicated jobs with one matrix-driven validation job.",
                expected_tradeoff="YAML becomes shorter and easier to maintain, but job logs move under matrix axes.",
            )
        )

    if root_has_lockfile(root):
        cache_missing = False
        for workflow in workflows:
            if any(step.kind == "uses" and "setup-" in step.value for job in workflow.jobs for step in job.steps):
                if not workflow_has_cache_signal(workflow):
                    cache_missing = True
                    break
        if cache_missing:
            recommendations.append(
                PerformanceRecommendation(
                    kind="add-cache-strategy",
                    current_pattern="Lockfile-backed dependencies without explicit workflow cache configuration.",
                    issue="Dependencies may be reinstalled on every run even though a deterministic cache key is available.",
                    proposed_change="Use setup-action native cache support or actions/cache keyed to the repository lockfile.",
                    expected_tradeoff="Runs should become faster, but cache invalidation behavior must follow dependency changes.",
                )
            )

    repeated_bootstrap = []
    for workflow in workflows:
        repeated_bootstrap.extend(detect_repeated_setup_prefixes(workflow.jobs))
    if repeated_bootstrap:
        strongest = repeated_bootstrap[0]
        recommendations.append(
            PerformanceRecommendation(
                kind="extract-shared-bootstrap",
                current_pattern=", ".join(strongest["jobs"]),
                issue="Several jobs repeat the same setup and install prefix.",
                proposed_change="Extract the repeated bootstrap into a composite action or reusable workflow.",
                expected_tradeoff="Shared setup becomes easier to update, but debugging jumps across one more abstraction layer.",
            )
        )

    workspace_file = root / "pnpm-workspace.yaml"
    root_package = root / "package.json"
    apps_dir = root / "apps"
    packages_dir = root / "packages"
    workspace_detected = workspace_file.exists() or apps_dir.exists() and packages_dir.exists()
    if root_package.exists() and not workspace_detected:
        try:
            package_data = json.loads(root_package.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            package_data = {}
        workspace_detected = isinstance(package_data.get("workspaces"), list)
    if workspace_detected:
        recommendations.append(
            PerformanceRecommendation(
                kind="path-aware-fanout",
                current_pattern="Workspace-style repository structure detected.",
                issue="Every package may be paying for the same full CI path regardless of which paths changed.",
                proposed_change="Introduce path-aware workflow fan-out or reusable workflows targeted by package boundaries.",
                expected_tradeoff="PR feedback gets faster, but path filters need careful maintenance as the repo evolves.",
            )
        )

    return recommendations


def build_architecture_plan(workflows: list[LocalCiWorkflow]) -> dict[str, object]:
    recommendations: list[dict[str, object]] = []
    target_files: list[dict[str, object]] = []
    seen_recommendations: set[tuple[str, str]] = set()
    seen_targets: set[str] = set()

    for workflow in workflows:
        plan = build_split_plan(workflow.text, workflow_name=Path(workflow.path).name)
        for recommendation in plan["recommendations"]:
            key = (recommendation["kind"], recommendation["reason"])
            if key not in seen_recommendations:
                recommendations.append(recommendation)
                seen_recommendations.add(key)
        for target in plan["target_files"]:
            path = str(target["path"])
            if path not in seen_targets:
                target_files.append(target)
                seen_targets.add(path)

    return {
        "recommendations": recommendations,
        "target_files": target_files,
    }


def build_repair_queue(
    architecture_plan: dict[str, object],
    governance_findings: list[GovernanceFinding],
    local_verification_plan: dict[str, object],
    workflow_inventory: list[WorkflowInventoryRecord],
) -> list[RepairQueueItem]:
    queued: dict[str, RepairQueueItem] = {}

    architecture_targets = [item["path"] for item in architecture_plan.get("target_files", [])]
    if architecture_targets:
        queued["workflow-structure"] = RepairQueueItem(
            kind="workflow-structure",
            reason="Workflow responsibilities should be split or reshaped before deeper CI debugging.",
            evidence=tuple(architecture_targets),
        )

    floating_refs = [item.evidence for item in governance_findings if item.category == "floating-ref"]
    if floating_refs:
        queued["action-versioning"] = RepairQueueItem(
            kind="action-versioning",
            reason="Remote action refs should be pinned before trusting later CI behavior.",
            evidence=tuple(floating_refs),
        )

    governance_evidence = [item.evidence for item in governance_findings if item.category != "floating-ref"]
    if governance_evidence:
        queued["permissions-and-governance"] = RepairQueueItem(
            kind="permissions-and-governance",
            reason="Governance gaps should be closed before the workflow is treated as production-ready.",
            evidence=tuple(governance_evidence),
        )

    blockers = tuple(str(item) for item in local_verification_plan.get("blockers", []))
    if blockers:
        queued["environment-and-tooling"] = RepairQueueItem(
            kind="environment-and-tooling",
            reason="Local reproduction has environment or safety blockers that limit execution confidence.",
            evidence=blockers,
        )

    inventory_paths = tuple(item.path for item in workflow_inventory)
    if inventory_paths:
        queued["repository-quality-gates"] = RepairQueueItem(
            kind="repository-quality-gates",
            reason="Repository quality gates should be reproduced through the workflow-derived command surface.",
            evidence=inventory_paths,
        )

    ordered_items: list[RepairQueueItem] = []
    for kind in REPAIR_QUEUE_ORDER:
        item = queued.get(kind)
        if item:
            ordered_items.append(item)
    return ordered_items


def workflow_matches(workflow: LocalCiWorkflow, workflow_filter: str | None) -> bool:
    if not workflow_filter:
        return True
    lowered = workflow_filter.lower()
    return lowered in Path(workflow.path).name.lower() or lowered == workflow.name.lower()


def job_matches(job: WorkflowJob, job_filter: str | None) -> bool:
    if not job_filter:
        return True
    lowered = job_filter.lower()
    return lowered == job.job_id.lower() or lowered == job.name.lower()


def default_event_name(triggers: Iterable[str]) -> str:
    ordered = list(triggers)
    for preferred in ("push", "pull_request", "workflow_dispatch", "schedule"):
        if preferred in ordered:
            return preferred
    return ordered[0] if ordered else "push"


def build_act_command(
    workflow_path: Path,
    event_name: str,
    job_id: str | None = None,
    matrix_entries: list[str] | None = None,
    secret_file: Path | None = None,
    env_file: Path | None = None,
    input_file: Path | None = None,
    event_file: Path | None = None,
    container_architecture: str | None = None,
    artifact_server_path: Path | None = None,
    action_offline_mode: bool = False,
    platform_overrides: list[str] | None = None,
) -> str:
    parts = ["act", event_name, "-W", path_to_posix(workflow_path)]
    if job_id:
        parts.extend(["-j", job_id])
    for matrix_entry in matrix_entries or []:
        parts.extend(["--matrix", matrix_entry])
    if secret_file:
        parts.extend(["--secret-file", path_to_posix(secret_file)])
    if env_file:
        parts.extend(["--env-file", path_to_posix(env_file)])
    if input_file:
        parts.extend(["--input-file", path_to_posix(input_file)])
    if event_file:
        parts.extend(["-e", path_to_posix(event_file)])
    if container_architecture:
        parts.extend(["--container-architecture", container_architecture])
    if artifact_server_path:
        parts.extend(["--artifact-server-path", path_to_posix(artifact_server_path)])
    for platform_override in platform_overrides or []:
        parts.extend(["-P", platform_override])
    if action_offline_mode:
        parts.append("--action-offline-mode")
    return " ".join(parts)


def analyze_local_ci_plan(
    workflows: list[LocalCiWorkflow],
    environment: dict[str, bool],
    requested_mode: str,
    workflow_filter: str | None = None,
    job_filter: str | None = None,
    event_name: str | None = None,
    matrix_entries: list[str] | None = None,
    secret_file: Path | None = None,
    env_file: Path | None = None,
    input_file: Path | None = None,
    event_file: Path | None = None,
    container_architecture: str | None = None,
    artifact_server_path: Path | None = None,
    action_offline_mode: bool = False,
    platform_overrides: list[str] | None = None,
) -> dict[str, object]:
    if not workflows:
        return {
            "selected_mode": "unsupported",
            "runnable_commands": [],
            "skipped_steps": [],
            "blockers": ["No GitHub Actions workflows found under .github/workflows."],
            "overall_status": "blocked",
            "act_command": None,
        }

    filtered_workflows = [workflow for workflow in workflows if workflow_matches(workflow, workflow_filter)]
    if not filtered_workflows:
        return {
            "selected_mode": "unsupported",
            "runnable_commands": [],
            "skipped_steps": [],
            "blockers": ["No workflows matched the requested filter."],
            "overall_status": "blocked",
            "act_command": None,
        }

    runnable_commands: list[str] = []
    skipped_steps: list[dict[str, object]] = []
    blockers: list[str] = []
    scope_limits: list[str] = []
    has_validation_signal = False
    has_deploy_signal = False
    has_secret_reference = False

    for workflow in filtered_workflows:
        has_deploy_signal = has_deploy_signal or has_keyword(workflow.name, DEPLOY_KEYWORDS)
        has_secret_reference = has_secret_reference or "${{ secrets." in workflow.text
        for job in workflow.jobs:
            if not job_matches(job, job_filter):
                continue
            has_deploy_signal = has_deploy_signal or has_keyword(job.job_id, DEPLOY_KEYWORDS) or has_keyword(job.name, DEPLOY_KEYWORDS)
            for step in job.steps:
                if step.kind == "run":
                    runnable_commands.append(step.value)
                    has_validation_signal = has_validation_signal or has_keyword(step.value, VALIDATION_KEYWORDS)
                    has_deploy_signal = has_deploy_signal or has_keyword(step.value, DEPLOY_KEYWORDS)
                elif step.kind == "uses":
                    step_record = {"job": job.job_id, "value": step.value}
                    skipped_steps.append(step_record)
                    if not is_supported_act_use(step.value):
                        blockers.append(f"Unsupported uses step requires manual review: {step.value}")
                        scope_limits.append(f"Unsupported uses step was not treated as locally verified: {step.value}")

    if has_deploy_signal and not has_validation_signal:
        blockers.insert(0, "Deploy-only workflow cannot be safely simulated locally in version one.")
        scope_limits.append("Deploy-only workflows remain outside the safe local simulation scope.")

    if has_secret_reference and has_deploy_signal and secret_file is None:
        blockers.insert(0, "Secret-dependent workflow requires --secret-file or manual review before local act execution.")
        scope_limits.append("Secret-dependent deploy workflows cannot be safely simulated locally without --secret-file.")

    requested_event = event_name or default_event_name(filtered_workflows[0].triggers)
    act_allowed = environment.get("act", False) and environment.get("docker", False) and not blockers
    act_command = None
    if act_allowed:
        act_command = build_act_command(
            workflow_path=Path(filtered_workflows[0].path),
            event_name=requested_event,
            job_id=job_filter,
            matrix_entries=matrix_entries,
            secret_file=secret_file,
            env_file=env_file,
            input_file=input_file,
            event_file=event_file,
            container_architecture=container_architecture,
            artifact_server_path=artifact_server_path,
            action_offline_mode=action_offline_mode,
            platform_overrides=platform_overrides,
        )

    fatal_blockers = (has_deploy_signal and not has_validation_signal) or (has_secret_reference and has_deploy_signal and secret_file is None)

    if requested_mode == "act":
        selected_mode = "act" if act_command else "unsupported"
    elif requested_mode == "fallback":
        selected_mode = "unsupported" if fatal_blockers else ("fallback" if runnable_commands else "unsupported")
    else:
        if fatal_blockers:
            selected_mode = "unsupported"
        elif act_command and has_validation_signal:
            selected_mode = "act"
        elif runnable_commands:
            selected_mode = "fallback"
        else:
            selected_mode = "unsupported"

    overall_status = "planned"
    if selected_mode == "unsupported":
        overall_status = "blocked"

    return {
        "selected_mode": selected_mode,
        "runnable_commands": runnable_commands,
        "skipped_steps": skipped_steps,
        "blockers": blockers,
        "scope_limits": scope_limits,
        "overall_status": overall_status,
        "act_command": act_command,
        "event_name": requested_event,
    }


def truncate_output(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n...[truncated]..."


def run_shell_command(root: Path, command: str, max_output_chars: int) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        shell=True,
        check=False,
    )
    status = "passed" if completed.returncode == 0 else "failed"
    return {
        "command": command,
        "returncode": completed.returncode,
        "status": status,
        "stdout": truncate_output(completed.stdout, max_output_chars),
        "stderr": truncate_output(completed.stderr, max_output_chars),
    }


def run_fallback_commands(
    root: Path,
    commands: list[str],
    fail_fast: bool,
    max_output_chars: int,
) -> tuple[list[dict[str, object]], str]:
    results: list[dict[str, object]] = []
    overall_status = "passed"
    for command in commands:
        result = run_shell_command(root, command, max_output_chars=max_output_chars)
        results.append(result)
        if result["status"] != "passed":
            overall_status = "failed"
            if fail_fast:
                break
    return results, overall_status


def build_local_ci_payload(
    root: Path,
    workflows: list[LocalCiWorkflow],
    environment: dict[str, bool],
    plan: dict[str, object],
    results: list[dict[str, object]],
    overall_status: str,
) -> dict[str, object]:
    return {
        "project_root": str(root),
        "workflow_count": len(workflows),
        "workflows": [
            {
                "path": workflow.path,
                "name": workflow.name,
                "triggers": list(workflow.triggers),
                "jobs": [
                    {
                        "id": job.job_id,
                        "name": job.name,
                        "steps": [{"kind": step.kind, "value": step.value, "name": step.name} for step in job.steps],
                    }
                    for job in workflow.jobs
                ],
            }
            for workflow in workflows
        ],
        "environment": environment,
        **plan,
        "results": results,
        "overall_status": overall_status,
    }


def build_ci_orchestration_payload(
    root: Path,
    workflows: list[LocalCiWorkflow],
    include_local_plan: bool = False,
    workflow_filter: str | None = None,
    job_filter: str | None = None,
    event_name: str | None = None,
) -> dict[str, object]:
    filtered_workflows = [workflow for workflow in workflows if workflow_matches(workflow, workflow_filter)]
    workflow_inventory = build_workflow_inventory(filtered_workflows)
    architecture_plan = build_architecture_plan(filtered_workflows)
    governance_findings = detect_governance_findings(root, filtered_workflows)
    performance_plan = detect_performance_recommendations(root, filtered_workflows)

    if include_local_plan:
        local_verification_plan = analyze_local_ci_plan(
            workflows=filtered_workflows,
            environment=inspect_local_ci_environment(),
            requested_mode="auto",
            workflow_filter=workflow_filter,
            job_filter=job_filter,
            event_name=event_name,
        )
        local_scope_limits = list(local_verification_plan.get("scope_limits", []))
        local_scope_limits.append("Local verification plan was generated but not executed in this orchestration pass.")
        local_verification_plan = {
            **local_verification_plan,
            "scope_limits": local_scope_limits,
        }
    else:
        local_verification_plan = {
            "selected_mode": "not-requested",
            "runnable_commands": [],
            "skipped_steps": [],
            "blockers": [],
            "scope_limits": ["Local verification plan was not requested in this orchestration pass."],
            "overall_status": "planned",
            "act_command": None,
            "event_name": event_name or (default_event_name(filtered_workflows[0].triggers) if filtered_workflows else "push"),
        }

    repair_queue = build_repair_queue(
        architecture_plan=architecture_plan,
        governance_findings=governance_findings,
        local_verification_plan=local_verification_plan,
        workflow_inventory=workflow_inventory,
    )
    proposed_files = [item["path"] for item in architecture_plan.get("target_files", [])]

    scope_limits = list(local_verification_plan.get("scope_limits", []))
    if not filtered_workflows:
        scope_limits.append("No workflows matched the requested filter.")
    if not proposed_files:
        scope_limits.append("No file-topology changes were proposed from the current workflow signals.")

    return {
        "workflow_inventory": [asdict(item) for item in workflow_inventory],
        "architecture_plan": architecture_plan,
        "governance_findings": [asdict(item) for item in governance_findings],
        "performance_plan": [asdict(item) for item in performance_plan],
        "local_verification_plan": local_verification_plan,
        "repair_queue": [asdict(item) for item in repair_queue],
        "proposed_files": proposed_files,
        "scope_limits": scope_limits,
    }
