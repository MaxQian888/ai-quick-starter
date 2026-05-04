#!/usr/bin/env python3
"""Build a Codex or Claude Code agent team plan from a project brief."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TARGET_CHOICES = ("codex", "claude-code", "both")
TARGET_LABELS = {
    "codex": "Codex",
    "claude-code": "Claude Code",
    "both": "Codex and Claude Code",
}

# Claude Code model aliases per role.
CLAUDE_CODE_MODEL_BY_ROLE = {
    "default": "sonnet",
    "worker": "sonnet",
    "explorer": "haiku",
    "reviewer": "sonnet",
    "planner": "sonnet",
    "implementer": "sonnet",
    "archiver": "sonnet",
}

# Read-only Claude Code tools — used when sandbox_mode is read-only.
CLAUDE_CODE_READONLY_TOOLS = ["Read", "Grep", "Glob", "WebFetch", "WebSearch"]

# Workspace-write tool allowlist for write-capable subagents.
# Omitted entirely if the agent is meant to inherit everything.
CLAUDE_CODE_WRITE_TOOLS = ["Read", "Edit", "Write", "Bash", "Grep", "Glob", "WebFetch"]

# Display colors keyed by role for the Claude Code `color` field.
CLAUDE_CODE_COLOR_BY_ROLE = {
    "default": "blue",
    "worker": "green",
    "explorer": "cyan",
    "reviewer": "purple",
    "planner": "yellow",
    "implementer": "orange",
    "archiver": "pink",
}


TASK_CATALOG = [
    {
        "id": "research",
        "title": "Research",
        "keywords": ["research", "investigate", "explore", "competitor", "discovery", "analyze"],
        "role": "explorer",
        "phase": "discovery",
        "reads_from": ["brief", "external-sources"],
        "writes_to": ["notes", "findings"],
        "parallelizable": True,
        "description": "Read the landscape and gather constraints before implementation starts.",
    },
    {
        "id": "documentation",
        "title": "Documentation",
        "keywords": ["documentation", "document", "docs", "spec", "manual", "guide"],
        "role": "default",
        "phase": "synthesis",
        "reads_from": ["brief", "research-notes", "implementation-status"],
        "writes_to": ["docs"],
        "parallelizable": True,
        "description": "Draft specs, user guides, or internal docs from the active workstream.",
    },
    {
        "id": "database",
        "title": "Database",
        "keywords": ["database", "schema", "sql", "migration", "mysql", "postgres", "db"],
        "role": "worker",
        "phase": "implementation",
        "reads_from": ["requirements", "research-notes"],
        "writes_to": ["database"],
        "parallelizable": True,
        "description": "Design or implement persistence models, schemas, and migrations.",
    },
    {
        "id": "data-collection",
        "title": "Data Collection",
        "keywords": ["collect data", "seed data", "dataset", "scrape", "crawl", "fetch data", "public sites"],
        "role": "explorer",
        "phase": "discovery",
        "reads_from": ["brief", "external-sources"],
        "writes_to": ["dataset", "raw-findings"],
        "parallelizable": True,
        "description": "Gather source material or seed data needed by downstream tasks.",
    },
    {
        "id": "frontend",
        "title": "Frontend",
        "keywords": ["frontend", "front-end", "ui", "page", "pages", "react", "next.js", "web app"],
        "role": "worker",
        "phase": "implementation",
        "reads_from": ["requirements", "design-assets", "research-notes"],
        "writes_to": ["frontend"],
        "parallelizable": True,
        "description": "Implement screens, components, and client-side behavior.",
    },
    {
        "id": "backend",
        "title": "Backend",
        "keywords": ["backend", "back-end", "api", "server", "service", "endpoint"],
        "role": "worker",
        "phase": "implementation",
        "reads_from": ["requirements", "research-notes", "database"],
        "writes_to": ["backend"],
        "parallelizable": True,
        "description": "Implement APIs, services, and server-side orchestration.",
    },
    {
        "id": "debugging",
        "title": "Debugging",
        "keywords": ["debug", "debugging", "fix", "triage", "integration issue", "bug"],
        "role": "worker",
        "phase": "verification",
        "reads_from": ["logs", "frontend", "backend", "database"],
        "writes_to": ["fixes", "regression-notes"],
        "parallelizable": False,
        "description": "Stabilize the integration surface and resolve regressions.",
    },
    {
        "id": "testing",
        "title": "Testing",
        "keywords": ["test", "testing", "qa", "verify", "validation"],
        "role": "worker",
        "phase": "verification",
        "reads_from": ["frontend", "backend", "database"],
        "writes_to": ["tests", "verification-results"],
        "parallelizable": False,
        "description": "Add or run checks that verify the merged behavior.",
    },
]

PHASE_ORDER = {"discovery": 0, "implementation": 1, "synthesis": 2, "verification": 3}
DEFAULT_MODELS = {"default": "gpt-5.4", "worker": "gpt-5.4", "explorer": "gpt-5.4", "reviewer": "gpt-5.4"}
WORKFLOW_PROFILE_CHOICES = ("auto", "generic", "superpowers-plan", "openspec-core", "openspec-expanded")
SUPERPOWERS_SIGNAL_MAP = {
    "superpowers:brainstorming": "brainstorming",
    "superpowers:writing-plans": "writing-plans",
    "superpowers:subagent-driven-development": "subagent-driven-development",
    "superpowers:executing-plans": "executing-plans",
    "verification-before-completion": "verification-before-completion",
    "superpowers:verification-before-completion": "verification-before-completion",
}
OPENSPEC_CORE_SIGNALS = ["/opsx:propose", "/opsx:apply", "/opsx:archive", "openspec"]
OPENSPEC_EXPANDED_SIGNALS = [
    "/opsx:explore",
    "/opsx:new",
    "/opsx:continue",
    "/opsx:ff",
    "/opsx:verify",
    "/opsx:sync",
    "/opsx:bulk-archive",
    "/opsx:onboard",
]
WORKFLOW_INTEGRATIONS = {
    "generic": [],
    "superpowers-plan": [
        {"id": "superpowers:brainstorming", "type": "skill", "phase": "design", "summary": "Design before implementation."},
        {"id": "superpowers:writing-plans", "type": "skill", "phase": "planning", "summary": "Turn the approved design into an implementation plan."},
        {
            "id": "superpowers:subagent-driven-development",
            "type": "skill",
            "phase": "execution",
            "summary": "Execute independent plan tasks with implementer and reviewer subagents in the same session.",
        },
        {
            "id": "superpowers:executing-plans",
            "type": "skill",
            "phase": "execution-fallback",
            "summary": "Fallback when tasks are tightly coupled or subagents are unavailable.",
        },
        {
            "id": "superpowers:verification-before-completion",
            "type": "skill",
            "phase": "verification",
            "summary": "Require fresh verification before claiming completion.",
        },
    ],
    "openspec-core": [
        {"id": "opsx:propose", "type": "command", "phase": "planning", "summary": "Create the change and planning artifacts."},
        {"id": "opsx:apply", "type": "command", "phase": "execution", "summary": "Implement tasks while updating artifacts as needed."},
        {"id": "opsx:archive", "type": "command", "phase": "closeout", "summary": "Archive the completed change and sync specs if required."},
    ],
    "openspec-expanded": [
        {"id": "opsx:explore", "type": "command", "phase": "discovery", "summary": "Think through requirements and options before planning."},
        {"id": "opsx:new", "type": "command", "phase": "planning", "summary": "Scaffold a new change without filling every artifact at once."},
        {"id": "opsx:continue", "type": "command", "phase": "planning", "summary": "Create the next artifact when its dependencies are ready."},
        {"id": "opsx:ff", "type": "command", "phase": "planning", "summary": "Fast-forward planning artifacts when the scope is already clear."},
        {"id": "opsx:apply", "type": "command", "phase": "execution", "summary": "Implement tasks while keeping artifacts in sync."},
        {"id": "opsx:verify", "type": "command", "phase": "verification", "summary": "Validate implementation against artifacts."},
        {"id": "opsx:sync", "type": "command", "phase": "sync", "summary": "Sync delta specs to the main spec set when needed."},
        {"id": "opsx:archive", "type": "command", "phase": "closeout", "summary": "Archive the completed change."},
    ],
}
WORKFLOW_STEPS = {
    "generic": [],
    "superpowers-plan": [
        {"id": "brainstorming", "title": "Brainstorming", "parallelizable": False, "notes": "Keep design clarification on the main thread."},
        {"id": "writing-plans", "title": "Writing Plans", "parallelizable": False, "notes": "Freeze file boundaries and task granularity before implementation."},
        {
            "id": "subagent-driven-development",
            "title": "Subagent Driven Development",
            "parallelizable": True,
            "notes": "Parallelize only independent implementation tasks and keep spec/code review checkpoints.",
        },
        {"id": "verification-before-completion", "title": "Verification Before Completion", "parallelizable": False, "notes": "Run fresh verification before completion claims."},
    ],
    "openspec-core": [
        {"id": "opsx:propose", "title": "Propose", "parallelizable": False, "notes": "Create planning artifacts before implementation."},
        {"id": "opsx:apply", "title": "Apply", "parallelizable": True, "notes": "Parallelize implementation only after artifacts are clear."},
        {"id": "opsx:archive", "title": "Archive", "parallelizable": False, "notes": "Close the change after implementation and verification."},
    ],
    "openspec-expanded": [
        {"id": "opsx:explore", "title": "Explore", "parallelizable": True, "notes": "Parallelize exploration, not artifact writes."},
        {"id": "opsx:new", "title": "New", "parallelizable": False, "notes": "Create the change scaffold."},
        {"id": "opsx:continue", "title": "Continue", "parallelizable": False, "notes": "Create the next dependency-ready artifact."},
        {"id": "opsx:ff", "title": "Fast Forward", "parallelizable": False, "notes": "Generate planning artifacts when the shape is already clear."},
        {"id": "opsx:apply", "title": "Apply", "parallelizable": True, "notes": "Parallelize implementation tasks only after artifacts are stable."},
        {"id": "opsx:verify", "title": "Verify", "parallelizable": False, "notes": "Validate work against artifacts before closeout."},
        {"id": "opsx:sync", "title": "Sync", "parallelizable": False, "notes": "Sync delta specs to the main spec set."},
        {"id": "opsx:archive", "title": "Archive", "parallelizable": False, "notes": "Archive after verification and sync decisions."},
    ],
}


@dataclass
class Task:
    task_id: str
    title: str
    role: str
    phase: str
    description: str
    parallelizable: bool
    reads_from: list[str]
    writes_to: list[str]
    depends_on: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.task_id,
            "title": self.title,
            "role": self.role,
            "phase": self.phase,
            "description": self.description,
            "parallelizable": self.parallelizable,
            "reads_from": self.reads_from,
            "writes_to": self.writes_to,
            "depends_on": self.depends_on,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Codex subagent team plan, matching JSON, and TOML drafts."
    )
    parser.add_argument("--input", default="", help="Path to the natural-language project brief.")
    parser.add_argument("--project-name", default="", help="Optional project label for output file names.")
    parser.add_argument("--output-dir", default="", help="Directory for generated outputs.")
    parser.add_argument("--config-file", default="", help="Optional shared config.toml to inspect.")
    parser.add_argument("--agents-dir", default="", help="Optional directory containing existing agent .toml files.")
    parser.add_argument("--agents-md", default="", help="Optional AGENTS.md file with routing rules.")
    parser.add_argument("--json-out", default="", help="Explicit JSON output path.")
    parser.add_argument("--markdown-out", default="", help="Explicit Markdown output path.")
    parser.add_argument(
        "--workflow-profile",
        default="auto",
        choices=WORKFLOW_PROFILE_CHOICES,
        help="Workflow profile to apply. auto detects generic, superpowers-plan, openspec-core, or openspec-expanded.",
    )
    parser.add_argument(
        "--target",
        default="codex",
        choices=TARGET_CHOICES,
        help=(
            "Which platform(s) to render agent files for. "
            "codex emits .toml drafts. claude-code emits Claude Code subagent .md files. "
            "both emits both formats."
        ),
    )
    parser.add_argument("--codex-home", default="", help="Override Codex home directory. Defaults to ~/.codex.")
    parser.add_argument(
        "--claude-home",
        default="",
        help="Override Claude Code home directory. Defaults to ~/.claude.",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help=(
            "Install generated agent files into the target platform(s). "
            "TOML drafts go to ~/.codex/agents/, Claude Code .md files go to ~/.claude/agents/."
        ),
    )
    parser.add_argument("--uninstall", action="store_true", help="Remove a previously installed team by manifest.")
    parser.add_argument("--manifest", default="", help="Explicit install manifest path for uninstall.")
    args = parser.parse_args(argv)
    if args.install and args.uninstall:
        parser.error("--install and --uninstall cannot be used together.")
    if not args.uninstall and not args.input:
        parser.error("--input is required unless --uninstall is used.")
    if args.uninstall and not args.project_name and not args.manifest:
        parser.error("--uninstall requires --project-name or --manifest.")
    return args


def normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("\r\n", "\n")
    return lowered


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "agents-team"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def detect_workflow_profile(brief_text: str, requested_profile: str) -> tuple[str, dict[str, Any]]:
    if requested_profile != "auto":
        return requested_profile, {"mode": "manual", "signals": [requested_profile], "summary": f"Workflow profile forced to {requested_profile}."}

    normalized = normalize_text(brief_text)
    expanded_hits = [signal for signal in OPENSPEC_EXPANDED_SIGNALS if signal in normalized]
    core_hits = [signal for signal in OPENSPEC_CORE_SIGNALS if signal in normalized]
    superpowers_hits = [signal for signal in SUPERPOWERS_SIGNAL_MAP if signal in normalized]

    if expanded_hits:
        return "openspec-expanded", {
            "mode": "auto",
            "signals": expanded_hits,
            "summary": "Detected expanded OpenSpec workflow cues from OPSX commands.",
        }
    if core_hits and any(signal.startswith("/opsx:") or signal == "openspec" for signal in core_hits):
        return "openspec-core", {
            "mode": "auto",
            "signals": core_hits,
            "summary": "Detected OpenSpec core workflow cues from OPSX commands or OpenSpec mentions.",
        }
    if superpowers_hits:
        return "superpowers-plan", {
            "mode": "auto",
            "signals": superpowers_hits,
            "summary": "Detected superpowers planning or execution skill cues.",
        }
    return "generic", {"mode": "auto", "signals": [], "summary": "No workflow-specific signals were detected."}


def detect_tasks(brief_text: str) -> list[Task]:
    normalized = normalize_text(brief_text)
    tasks: list[Task] = []
    seen_ids: set[str] = set()

    for item in TASK_CATALOG:
        if any(keyword in normalized for keyword in item["keywords"]):
            depends_on: list[str] = []
            if item["phase"] == "implementation":
                for dependency in ("research", "data-collection"):
                    if dependency in seen_ids:
                        depends_on.append(dependency)
            if item["phase"] == "synthesis":
                for dependency in ("research", "database", "frontend", "backend"):
                    if dependency in seen_ids:
                        depends_on.append(dependency)
            if item["phase"] == "verification":
                for dependency in ("database", "frontend", "backend"):
                    if dependency in seen_ids:
                        depends_on.append(dependency)

            tasks.append(
                Task(
                    task_id=item["id"],
                    title=item["title"],
                    role=item["role"],
                    phase=item["phase"],
                    description=item["description"],
                    parallelizable=item["parallelizable"],
                    reads_from=list(item["reads_from"]),
                    writes_to=list(item["writes_to"]),
                    depends_on=depends_on,
                )
            )
            seen_ids.add(item["id"])

    if not tasks:
        tasks.append(
            Task(
                task_id="planning",
                title="Planning",
                role="default",
                phase="discovery",
                description="Normalize the request, split the work, and define the first execution batch.",
                parallelizable=False,
                reads_from=["brief"],
                writes_to=["plan"],
                depends_on=[],
            )
        )

    research_present = any(task.task_id == "research" for task in tasks)
    data_present = any(task.task_id == "data-collection" for task in tasks)
    implementation_ids = {task.task_id for task in tasks if task.phase == "implementation"}
    for task in tasks:
        if task.phase == "implementation":
            task.depends_on = [dep for dep in ("research", "data-collection") if dep in {t.task_id for t in tasks}]
        elif task.phase == "synthesis":
            prior = []
            if research_present:
                prior.append("research")
            if data_present:
                prior.append("data-collection")
            if implementation_ids and task.title == "Documentation":
                prior.extend(sorted(implementation_ids))
            task.depends_on = prior
        elif task.phase == "verification":
            task.depends_on = sorted(implementation_ids) if implementation_ids else []

    return tasks


def build_parallel_groups(tasks: list[Task]) -> list[dict[str, Any]]:
    by_phase: dict[str, list[Task]] = {}
    for task in tasks:
        by_phase.setdefault(task.phase, []).append(task)

    groups: list[dict[str, Any]] = []
    for phase in ("discovery", "implementation", "synthesis", "verification"):
        phase_tasks = by_phase.get(phase, [])
        if not phase_tasks:
            continue
        parallel_tasks = [task for task in phase_tasks if task.parallelizable]
        if not parallel_tasks:
            continue
        groups.append(
            {
                "group_id": f"{phase}-batch",
                "goal": phase.capitalize(),
                "tasks": [task.task_id for task in parallel_tasks],
                "max_concurrency": len(parallel_tasks),
                "why_parallelizable": (
                    "These tasks share the same phase and do not require one another's immediate writes."
                ),
                "merge_point": (
                    "Review outputs from this batch before handing off to the next phase."
                    if phase != "verification"
                    else "Merge fixes and rerun verification before completion."
                ),
            }
        )
    return groups


def build_agents(tasks: list[Task]) -> list[dict[str, Any]]:
    task_ids_by_role: dict[str, list[str]] = {"default": [], "worker": [], "explorer": []}
    for task in tasks:
        task_ids_by_role.setdefault(task.role, []).append(task.task_id)

    agents = [
        {
            "name": "default",
            "role": "default",
            "purpose": "Fallback synthesis, documentation, and integration support.",
            "model": DEFAULT_MODELS["default"],
            "reasoning_effort": "high",
            "sandbox_mode": "workspace-write",
            "nickname_candidates": ["Atlas", "Delta", "Echo"],
            "developer_instructions": (
                "Answer in the user's working language. Preserve code, commands, and logs verbatim. "
                "Handle synthesis, planning, and cross-task cleanup without drifting into unrelated work."
            ),
            "owns_tasks": sorted(task_ids_by_role.get("default", [])),
            "reads_from": ["brief", "research-notes", "implementation-status"],
            "writes_to": ["docs", "summaries", "handoff-notes"],
        },
        {
            "name": "worker",
            "role": "worker",
            "purpose": "Execution-focused implementation and fixes.",
            "model": DEFAULT_MODELS["worker"],
            "reasoning_effort": "high",
            "sandbox_mode": "workspace-write",
            "nickname_candidates": ["Forge", "Relay", "Nova"],
            "developer_instructions": (
                "Implement only the assigned scope. Validate touched files. Do not revert work owned by other agents. "
                "Call out blocked dependencies instead of guessing."
            ),
            "owns_tasks": sorted(task_ids_by_role.get("worker", [])),
            "reads_from": ["brief", "research-notes", "existing-code"],
            "writes_to": ["source-code", "tests", "fixes"],
        },
        {
            "name": "explorer",
            "role": "explorer",
            "purpose": "Read-heavy exploration, mapping, and evidence gathering.",
            "model": DEFAULT_MODELS["explorer"],
            "reasoning_effort": "high",
            "sandbox_mode": "read-only",
            "nickname_candidates": ["Scout", "Trace", "Lens"],
            "developer_instructions": (
                "Stay in exploration mode. Read, map, and report findings without editing files. "
                "Surface uncertainty and likely next reads."
            ),
            "owns_tasks": sorted(task_ids_by_role.get("explorer", [])),
            "reads_from": ["brief", "repositories", "docs", "public-sources"],
            "writes_to": ["findings", "indices", "research-notes"],
        },
    ]

    if any(task.phase == "verification" for task in tasks):
        agents.append(
            {
                "name": "reviewer",
                "role": "reviewer",
                "purpose": "Review and regression-focused quality pass.",
                "model": DEFAULT_MODELS["reviewer"],
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Audit", "Guard", "Pulse"],
                "developer_instructions": (
                    "Review outputs for regressions, missing tests, and unsafe assumptions. "
                    "Prefer targeted verification and concise findings."
                ),
                "owns_tasks": [task.task_id for task in tasks if task.phase == "verification"],
                "reads_from": ["diff", "tests", "logs"],
                "writes_to": ["review-findings", "regression-tests"],
            }
        )

    return agents


def workflow_custom_agents(profile: str) -> list[dict[str, Any]]:
    if profile == "superpowers-plan":
        return [
            {
                "name": "planner",
                "role": "planner",
                "purpose": "Turn approved specs into execution-ready plans and chunk boundaries.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Draft", "Frame", "Map"],
                "developer_instructions": "Focus on implementation planning, explicit file boundaries, and bite-sized steps. Do not skip review checkpoints.",
                "owns_tasks": ["planning", "documentation"],
                "reads_from": ["specs", "requirements"],
                "writes_to": ["plans", "task-breakdowns"],
            },
            {
                "name": "implementer",
                "role": "implementer",
                "purpose": "Execute one scoped task at a time from the approved plan.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Forge", "Patch", "Shift"],
                "developer_instructions": "Implement only the assigned task, validate touched files, and ask for missing context instead of guessing.",
                "owns_tasks": ["frontend", "backend", "database", "testing"],
                "reads_from": ["plan", "code"],
                "writes_to": ["source-code", "tests"],
            },
            {
                "name": "spec-reviewer",
                "role": "reviewer",
                "purpose": "Review whether implementation still matches the approved spec and plan.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "read-only",
                "nickname_candidates": ["Spec Guard", "Trace", "Scope"],
                "developer_instructions": "Lead with missing requirements, unexpected behavior changes, and scope drift. Stay read-only.",
                "owns_tasks": ["spec-review"],
                "reads_from": ["specs", "diff"],
                "writes_to": ["findings"],
            },
            {
                "name": "quality-reviewer",
                "role": "reviewer",
                "purpose": "Review code quality, regression risk, and test gaps after spec compliance is clear.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "read-only",
                "nickname_candidates": ["Audit", "Pulse", "Guard"],
                "developer_instructions": "Focus on real risks, missing tests, and maintainability issues. Avoid style-only commentary.",
                "owns_tasks": ["quality-review"],
                "reads_from": ["diff", "tests", "logs"],
                "writes_to": ["findings"],
            },
            {
                "name": "final-reviewer",
                "role": "reviewer",
                "purpose": "Run the final branch-level pass before development is considered complete.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "read-only",
                "nickname_candidates": ["Final Gate", "Atlas", "Delta"],
                "developer_instructions": "Review the combined branch outcome, summarize residual risks, and confirm verification evidence exists.",
                "owns_tasks": ["final-review"],
                "reads_from": ["diff", "verification-results"],
                "writes_to": ["summary"],
            },
        ]
    if profile == "openspec-core":
        return [
            {
                "name": "proposal-writer",
                "role": "planner",
                "purpose": "Own the proposal and change framing for OpenSpec propose.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Pitch", "Frame", "Intent"],
                "developer_instructions": "Write a clear proposal that captures intent, scope, and approach without prematurely implementing.",
                "owns_tasks": ["proposal"],
                "reads_from": ["brief", "project-context"],
                "writes_to": ["proposal.md"],
            },
            {
                "name": "spec-author",
                "role": "planner",
                "purpose": "Define requirement-level artifacts and scenarios.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Spec", "Scenario", "Clause"],
                "developer_instructions": "Convert the proposal into concrete requirements and scenarios without collapsing into implementation chatter.",
                "owns_tasks": ["specs"],
                "reads_from": ["proposal"],
                "writes_to": ["specs"],
            },
            {
                "name": "design-author",
                "role": "planner",
                "purpose": "Write or refine the technical design for the change.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Design", "Flow", "Bridge"],
                "developer_instructions": "Translate requirements into a concrete technical approach and call out dependencies or risks.",
                "owns_tasks": ["design"],
                "reads_from": ["proposal", "specs"],
                "writes_to": ["design.md"],
            },
            {
                "name": "task-planner",
                "role": "planner",
                "purpose": "Break the approved design into implementation tasks.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Task", "Grid", "Sprint"],
                "developer_instructions": "Write tasks that are executable, verifiable, and review-friendly. Keep dependencies explicit.",
                "owns_tasks": ["tasks"],
                "reads_from": ["design", "specs"],
                "writes_to": ["tasks.md"],
            },
            {
                "name": "archiver",
                "role": "archiver",
                "purpose": "Close the OpenSpec change cleanly after verification.",
                "model": "gpt-5.4",
                "reasoning_effort": "high",
                "sandbox_mode": "workspace-write",
                "nickname_candidates": ["Archive", "Vault", "Ledger"],
                "developer_instructions": "Archive only after implementation and verification are complete. Preserve artifact integrity and sync decisions.",
                "owns_tasks": ["archive"],
                "reads_from": ["change-artifacts", "verification-results"],
                "writes_to": ["archive"],
            },
        ]
    if profile == "openspec-expanded":
        agents = workflow_custom_agents("openspec-core")
        agents.extend(
            [
                {
                    "name": "workflow-explorer",
                    "role": "explorer",
                    "purpose": "Own the exploratory OpenSpec steps before artifacts are written.",
                    "model": "gpt-5.4-mini",
                    "reasoning_effort": "medium",
                    "sandbox_mode": "read-only",
                    "nickname_candidates": ["Explore", "Scout", "Lens"],
                    "developer_instructions": "Investigate options, edge cases, and repository context without editing files.",
                    "owns_tasks": ["explore"],
                    "reads_from": ["brief", "repo"],
                    "writes_to": ["findings"],
                },
                {
                    "name": "verifier",
                    "role": "reviewer",
                    "purpose": "Run the OpenSpec verify pass against artifacts and implementation.",
                    "model": "gpt-5.4",
                    "reasoning_effort": "high",
                    "sandbox_mode": "read-only",
                    "nickname_candidates": ["Verify", "Check", "Proof"],
                    "developer_instructions": "Compare implementation against artifacts and report any mismatch before archive.",
                    "owns_tasks": ["verify"],
                    "reads_from": ["artifacts", "diff", "tests"],
                    "writes_to": ["verification-results"],
                },
                {
                    "name": "sync-manager",
                    "role": "planner",
                    "purpose": "Manage spec sync decisions before archiving expanded OpenSpec changes.",
                    "model": "gpt-5.4",
                    "reasoning_effort": "high",
                    "sandbox_mode": "workspace-write",
                    "nickname_candidates": ["Sync", "Merge", "Align"],
                    "developer_instructions": "Sync delta specs into the main spec set carefully and avoid losing artifact intent.",
                    "owns_tasks": ["sync"],
                    "reads_from": ["delta-specs", "main-specs"],
                    "writes_to": ["synced-specs"],
                },
            ]
        )
        return agents
    return []


def build_prompts(agents: list[dict[str, Any]], tasks: list[Task]) -> list[dict[str, Any]]:
    title_by_id = {task.task_id: task.title for task in tasks}
    prompts: list[dict[str, Any]] = []
    for agent in agents:
        task_titles = [title_by_id[task_id] for task_id in agent["owns_tasks"] if task_id in title_by_id]
        if task_titles:
            scope = ", ".join(task_titles)
        else:
            scope = "integration support and overflow tasks"
        prompts.append(
            {
                "agent": agent["name"],
                "prompt": (
                    f"Use the {agent['name']} agent to handle {scope}. "
                    f"Keep ownership clear, stay within the assigned write scope, and report blockers early."
                ),
            }
        )
    return prompts


def enrich_agents_for_profile(base_agents: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    seen = {agent["name"] for agent in base_agents}
    for agent in workflow_custom_agents(profile):
        if agent["name"] not in seen:
            base_agents.append(agent)
            seen.add(agent["name"])
    return base_agents


def build_execution_plan(tasks: list[Task]) -> list[dict[str, Any]]:
    ordered = sorted(tasks, key=lambda item: (PHASE_ORDER[item.phase], item.title))
    plan: list[dict[str, Any]] = []
    for index, task in enumerate(ordered, start=1):
        plan.append(
            {
                "step": index,
                "task_id": task.task_id,
                "title": task.title,
                "phase": task.phase,
                "depends_on": task.depends_on,
                "handoff": (
                    "Merge with the next phase only after outputs are reviewed."
                    if task.parallelizable
                    else "Complete and verify before proceeding."
                ),
            }
        )
    return plan


def build_assumptions(
    input_path: Path,
    args: argparse.Namespace,
    tasks: list[Task],
    workflow_profile: str,
) -> list[str]:
    target_label = TARGET_LABELS.get(args.target, args.target)
    if args.target == "claude-code":
        artifact_phrase = "Claude Code subagent .md drafts"
        install_phrase = "into ~/.claude/agents/"
    elif args.target == "both":
        artifact_phrase = "Codex .toml drafts and Claude Code subagent .md drafts"
        install_phrase = "into ~/.codex/agents/ and ~/.claude/agents/"
    else:
        artifact_phrase = "Codex .toml drafts"
        install_phrase = "into the target Codex agents directory"

    assumptions = [
        f"Used {input_path.name} as the primary request source.",
        f"Targeted {target_label} for agent file generation.",
        "This first-pass plan uses keyword heuristics instead of a semantic dependency graph.",
        (
            f"Generated {artifact_phrase} are reviewable drafts and are not installed automatically."
            if not args.install
            else f"Install mode was explicitly requested, so generated {artifact_phrase} were copied {install_phrase}."
        ),
    ]
    if args.target in ("claude-code", "both"):
        assumptions.append(
            "Claude Code agent teams are experimental — the generated team brief is a paste-in spawn prompt, "
            "not a pre-authored team config (~/.claude/teams/<team>/config.json is auto-managed runtime state)."
        )
    if args.config_file:
        assumptions.append(f"Inspected existing config.toml context from {args.config_file}.")
    if args.agents_dir:
        assumptions.append(f"Inspected existing per-agent drafts in {args.agents_dir}.")
    if args.agents_md:
        assumptions.append(f"Inspected AGENTS instructions from {args.agents_md}.")
    if any(task.phase == "verification" for task in tasks):
        assumptions.append("Verification work was split into its own phase to avoid false parallelism.")
    if workflow_profile != "generic":
        assumptions.append(f"Applied the {workflow_profile} workflow profile to shape extra roles and workflow steps.")
    return assumptions


def build_risks(tasks: list[Task], workflow_profile: str) -> list[str]:
    risks = [
        "Too many write-capable agents on overlapping files will erase the value of parallelization.",
        "If a task's immediate next action depends on another task's output, it should stay serial.",
        "Generated model and prompt choices are defaults, not guarantees of actual runtime selection.",
    ]
    if sum(task.phase == "implementation" for task in tasks) > 1:
        risks.append("Frontend, backend, and database work need an explicit merge point before debugging or QA.")
    if workflow_profile == "superpowers-plan":
        risks.append("Do not skip from planning straight to implementation; superpowers expects design and plan checkpoints first.")
    if workflow_profile.startswith("openspec"):
        risks.append("Do not parallelize artifact-authoring commands and implementation in the same uncontrolled batch.")
    if workflow_profile == "openspec-expanded":
        risks.append("Verify and sync are closeout gates; they should not run concurrently with active feature implementation.")
    return risks


def build_open_questions(tasks: list[Task], workflow_profile: str, target: str = "codex") -> list[str]:
    questions = [
        "Are there repository-specific instructions that should be merged into developer_instructions?",
    ]
    if target in ("codex", "both"):
        questions.append("Should any custom Codex agents be promoted from drafts into persistent ~/.codex/agents/*.toml files?")
    if target in ("claude-code", "both"):
        questions.append(
            "Should the Claude Code subagents live at the project scope (.claude/agents/) so the team can review them, "
            "or stay at the user scope (~/.claude/agents/) for personal reuse?"
        )
        questions.append(
            "Do any subagents need stricter tool restrictions (disallowedTools) or permission modes "
            "(plan, acceptEdits) before being trusted as agent-team teammates?"
        )
    if any(task.title == "Data Collection" for task in tasks):
        questions.append("Does data collection require credentials, APIs, or legal review before delegation?")
    if workflow_profile == "superpowers-plan":
        questions.append("Should the execution path use subagent-driven-development or executing-plans for this repository state?")
    if workflow_profile.startswith("openspec"):
        questions.append("Does this repository use the core OpenSpec profile or the expanded OPSX command set in practice?")
    return questions


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render_toml(agent: dict[str, Any]) -> str:
    lines = [
        f'name = "{toml_escape(agent["name"])}"',
        f'description = "{toml_escape(agent["purpose"])}"',
        f'model = "{toml_escape(agent["model"])}"',
        f'model_reasoning_effort = "{toml_escape(agent["reasoning_effort"])}"',
        "tool_output_token_limit = 40000",
        'model_reasoning_summary = "detailed"',
        'model_verbosity = "high"',
        "model_supports_reasoning_summaries = true",
        'service_tier = "fast"',
    ]
    if agent["sandbox_mode"] == "read-only":
        lines.append('sandbox_mode = "read-only"')
    lines.append(
        "nickname_candidates = ["
        + ", ".join(f'"{toml_escape(item)}"' for item in agent["nickname_candidates"])
        + "]"
    )
    lines.append('developer_instructions = """')
    lines.extend(agent["developer_instructions"].splitlines())
    lines.append('"""')
    return "\n".join(lines) + "\n"


def claude_code_agent_name(name: str) -> str:
    """Claude Code requires lowercase letters and hyphens for subagent names."""
    cleaned = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return cleaned or "agent"


def claude_code_tools_for_agent(agent: dict[str, Any]) -> list[str]:
    """Pick the Claude Code tool allowlist for an agent.

    Read-only sandbox -> read-only tools.
    Workspace-write sandbox -> a conservative write toolset. The user can
    delete the field manually to inherit every tool from the parent session.
    """
    sandbox = agent.get("sandbox_mode", "workspace-write")
    if sandbox == "read-only":
        return list(CLAUDE_CODE_READONLY_TOOLS)
    return list(CLAUDE_CODE_WRITE_TOOLS)


def claude_code_model_for_agent(agent: dict[str, Any]) -> str:
    """Map our internal role to a Claude Code model alias."""
    role = agent.get("role", "default")
    return CLAUDE_CODE_MODEL_BY_ROLE.get(role, "sonnet")


def claude_code_description(agent: dict[str, Any]) -> str:
    """Build a description that nudges Claude to delegate proactively."""
    purpose = agent.get("purpose", "").strip()
    if not purpose:
        purpose = f"{agent['name']} subagent."
    if not purpose.endswith("."):
        purpose += "."
    role = agent.get("role", "default")
    if role == "explorer":
        nudge = "Use proactively for read-heavy exploration, codebase mapping, or documentation review."
    elif role == "reviewer":
        nudge = "Use proactively to review work for regressions, missing tests, or scope drift before completion."
    elif role == "planner":
        nudge = "Use proactively when turning specs or briefs into actionable plans with explicit file boundaries."
    elif role == "implementer" or role == "worker":
        nudge = "Use when an approved plan or task scope is ready for focused implementation."
    elif role == "archiver":
        nudge = "Use only after implementation and verification are complete to close out the change cleanly."
    else:
        nudge = "Use for synthesis, integration, and cross-task cleanup."
    return f"{purpose} {nudge}"


def render_claude_code_agent(agent: dict[str, Any]) -> str:
    """Render a Claude Code subagent file as Markdown with YAML frontmatter."""
    cc_name = claude_code_agent_name(agent["name"])
    description = claude_code_description(agent).replace("\n", " ").strip()
    tools = ", ".join(claude_code_tools_for_agent(agent))
    model = claude_code_model_for_agent(agent)
    color = CLAUDE_CODE_COLOR_BY_ROLE.get(agent.get("role", "default"))

    lines: list[str] = ["---"]
    lines.append(f"name: {cc_name}")
    lines.append(f"description: {description}")
    if tools:
        lines.append(f"tools: {tools}")
    lines.append(f"model: {model}")
    if color:
        lines.append(f"color: {color}")
    lines.append("---")
    lines.append("")

    body_parts: list[str] = []
    purpose = agent.get("purpose", "").strip()
    if purpose:
        body_parts.append(f"You are the **{cc_name}** subagent. {purpose}")
    instructions = agent.get("developer_instructions", "").strip()
    if instructions:
        body_parts.append(instructions)

    owns = agent.get("owns_tasks") or []
    if owns:
        body_parts.append("## Scope\n\nYou own these tasks:\n" + "\n".join(f"- {item}" for item in owns))

    reads = agent.get("reads_from") or []
    writes = agent.get("writes_to") or []
    io_lines: list[str] = []
    if reads:
        io_lines.append("- Reads: " + ", ".join(reads))
    if writes:
        io_lines.append("- Writes: " + ", ".join(writes))
    if io_lines:
        body_parts.append("## I/O Contract\n\n" + "\n".join(io_lines))

    body_parts.append(
        "## Operating Principles\n\n"
        "- Stay inside your assigned scope; flag blockers instead of guessing.\n"
        "- Preserve code, commands, and logs verbatim when reporting back.\n"
        "- When working as part of an agent team, coordinate via the shared task list and SendMessage rather than duplicating work."
    )

    lines.extend((part.rstrip() + "\n") for part in body_parts)
    return "\n".join(lines).rstrip() + "\n"


def build_team_brief(payload: dict[str, Any]) -> str:
    """Generate a natural-language brief that the user can paste into Claude Code
    to spawn an experimental agent team.

    Per the Claude Code docs the team config (~/.claude/teams/{team}/config.json)
    is auto-managed runtime state and must not be pre-authored, so we deliberately
    emit a prompt rather than a config file.
    """
    project_name = payload["request"]["project_name"]
    workflow_profile = payload["workflow_profile"]
    agents = payload["agents"]
    parallel_groups = payload["parallel_groups"]
    execution_plan = payload["execution_plan"]
    risks = payload["risks"]

    lines: list[str] = []
    lines.append(f"# Agent Team Brief: {project_name}")
    lines.append("")
    lines.append("> Paste this brief into a Claude Code session that has agent teams enabled")
    lines.append("> (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) and Claude Code v2.1.32 or later.")
    lines.append("> The lead session will spawn teammates that reuse the subagent definitions")
    lines.append("> generated alongside this brief.")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(payload["request"]["source_summary"].strip() or f"Coordinate work on {project_name}.")
    lines.append("")
    lines.append(f"## Workflow Profile: `{workflow_profile}`")
    lines.append("")
    lines.append(payload["workflow_detection"].get("summary", "").strip())
    lines.append("")
    lines.append("## Spawn These Teammates")
    lines.append("")
    for agent in agents:
        cc_name = claude_code_agent_name(agent["name"])
        owns = ", ".join(agent.get("owns_tasks") or []) or "integration support"
        lines.append(
            f"- Spawn a teammate using the `{cc_name}` subagent type. "
            f"Scope: {owns}. Purpose: {agent.get('purpose', '').strip()}"
        )
    lines.append("")
    if parallel_groups:
        lines.append("## Parallel Batches")
        lines.append("")
        for group in parallel_groups:
            lines.append(
                f"- `{group['group_id']}`: run {', '.join(group['tasks'])} in parallel; "
                f"merge point — {group['merge_point']}"
            )
        lines.append("")
    if execution_plan:
        lines.append("## Execution Order")
        lines.append("")
        for step in execution_plan:
            depends = ", ".join(step["depends_on"]) if step["depends_on"] else "none"
            lines.append(f"{step['step']}. {step['title']} ({step['phase']}; depends on: {depends})")
        lines.append("")
    lines.append("## Coordination Rules")
    lines.append("")
    lines.append("- Use the shared task list to claim and track work; do not edit the same file from two teammates.")
    lines.append("- Reviewer teammates should run after implementation merges, not concurrently with active edits.")
    lines.append("- Ask teammates to report blockers via SendMessage instead of busy-waiting.")
    lines.append("- Tell the lead `Clean up the team` when work is complete; do not delete `~/.claude/teams/<team>/` by hand.")
    lines.append("")
    if risks:
        lines.append("## Watch For")
        lines.append("")
        for risk in risks:
            lines.append(f"- {risk}")
        lines.append("")
    lines.append("## Suggested Lead Prompt")
    lines.append("")
    spawn_lines = [
        f"Create an agent team for `{project_name}`.",
        "Use the following subagent definitions as teammate roles:",
    ]
    for agent in agents:
        spawn_lines.append(f"- `{claude_code_agent_name(agent['name'])}` — {agent.get('purpose', '').strip()}")
    spawn_lines.append("")
    spawn_lines.append("Honor the parallel batches and execution order above. Stop and ask before merging cross-cutting changes.")
    lines.append("```text")
    lines.extend(spawn_lines)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    project_name = payload["request"]["project_name"]
    lines.append(f"# {project_name} Agents Team Plan")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append(payload["request"]["source_summary"])
    lines.append("")
    lines.append("## Assumptions")
    lines.append("")
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Workflow Profile")
    lines.append("")
    lines.append(f"- Profile: `{payload['workflow_profile']}`")
    lines.append(f"- Detection: {payload['workflow_detection']['summary']}")
    for signal in payload["workflow_detection"]["signals"]:
        lines.append(f"- Signal: `{signal}`")
    lines.append("")
    if payload["workflow_steps"]:
        lines.append("## Workflow Steps")
        lines.append("")
        for step in payload["workflow_steps"]:
            lines.append(
                f"- `{step['id']}`: {step['title']} (parallelizable: {str(step['parallelizable']).lower()}) - {step['notes']}"
            )
        lines.append("")
    if payload["workflow_integrations"]:
        lines.append("## Workflow Integrations")
        lines.append("")
        for item in payload["workflow_integrations"]:
            lines.append(f"- `{item['id']}` ({item['type']}, {item['phase']}): {item['summary']}")
        lines.append("")
    lines.append("## Task Decomposition")
    lines.append("")
    for task in payload["task_graph"]:
        lines.append(
            f"- `{task['id']}`: {task['title']} ({task['phase']}, role `{task['role']}`)"
        )
    lines.append("")
    lines.append("## Parallelization Plan")
    lines.append("")
    for group in payload["parallel_groups"]:
        lines.append(
            f"- `{group['group_id']}`: tasks {', '.join(group['tasks'])}; merge point: {group['merge_point']}"
        )
    if not payload["parallel_groups"]:
        lines.append("- No safe parallel groups were detected from the current brief.")
    lines.append("")
    lines.append("## Agent Team")
    lines.append("")
    for agent in payload["agents"]:
        lines.append(
            f"- `{agent['name']}` ({agent['role']}): {agent['purpose']} Owns: {', '.join(agent['owns_tasks']) or 'none'}"
        )
    lines.append("")
    lines.append("## Prompt Templates")
    lines.append("")
    for prompt in payload["prompts"]:
        lines.append(f"- `{prompt['agent']}`: {prompt['prompt']}")
    lines.append("")
    if payload.get("toml_files"):
        lines.append("## TOML Drafts")
        lines.append("")
        for file_name, record in payload["toml_files"].items():
            lines.append(f"### {file_name}")
            lines.append("")
            lines.append("```toml")
            lines.append(record["content"].rstrip())
            lines.append("```")
            lines.append("")
    if payload.get("claude_code_files"):
        lines.append("## Claude Code Subagent Files")
        lines.append("")
        for file_name, record in payload["claude_code_files"].items():
            lines.append(f"### {file_name}")
            lines.append("")
            lines.append("```markdown")
            lines.append(record["content"].rstrip())
            lines.append("```")
            lines.append("")
    if payload.get("team_brief"):
        lines.append("## Claude Code Team Brief")
        lines.append("")
        lines.append("```markdown")
        lines.append(payload["team_brief"]["content"].rstrip())
        lines.append("```")
        lines.append("")
    if payload["install_manifest"]:
        lines.append("## Install Management")
        lines.append("")
        manifests = payload["install_manifest"]
        if isinstance(manifests, list):
            for manifest in manifests:
                lines.append(f"- {manifest.get('target', '?')} manifest: `{manifest['path']}`")
        else:
            lines.append(f"- Manifest: `{manifests['path']}`")
        for item in payload["installed_files"]:
            detail = item["action"]
            if item.get("backup_path"):
                detail += f", backup: {item['backup_path']}"
            target_label = f"[{item.get('target', 'codex')}] " if item.get("target") else ""
            lines.append(f"- {target_label}`{item['file_name']}` -> `{item['destination_path']}` ({detail})")
        lines.append("")
    lines.append("## Execution Order")
    lines.append("")
    for step in payload["execution_plan"]:
        depends = ", ".join(step["depends_on"]) if step["depends_on"] else "none"
        lines.append(f"- Step {step['step']}: {step['title']} (depends on: {depends})")
    lines.append("")
    lines.append("## Risks And Guardrails")
    lines.append("")
    for risk in payload["risks"]:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("## Open Questions")
    lines.append("")
    for question in payload["open_questions"]:
        lines.append(f"- {question}")
    lines.append("")
    return "\n".join(lines)


def ensure_output_dir(args: argparse.Namespace, project_slug: str) -> Path:
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(tempfile.mkdtemp(prefix=f"{project_slug}-agents-team-"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def resolve_codex_home(args: argparse.Namespace) -> Path:
    if args.codex_home:
        codex_home = Path(args.codex_home)
    else:
        codex_home = Path.home() / ".codex"
    codex_home.mkdir(parents=True, exist_ok=True)
    return codex_home


def resolve_claude_home(args: argparse.Namespace) -> Path:
    if args.claude_home:
        claude_home = Path(args.claude_home)
    else:
        claude_home = Path.home() / ".claude"
    claude_home.mkdir(parents=True, exist_ok=True)
    return claude_home


def manifest_root(codex_home: Path) -> Path:
    return codex_home / "agents" / ".agents-team-builder"


def build_manifest_path(project_slug: str, codex_home: Path) -> Path:
    return manifest_root(codex_home) / "manifests" / f"{project_slug}.json"


def _install_target_files(
    *,
    target: str,
    home: Path,
    files: dict[str, dict[str, Any]],
    payload: dict[str, Any],
    json_out: Path,
    stamp: str,
) -> dict[str, Any]:
    """Copy files into <home>/agents/, recording backups + manifest under
    <home>/agents/.agents-team-builder/. Returns one manifest descriptor."""
    project_slug = payload["request"]["project_slug"]
    agents_dir = home / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    root = manifest_root(home)
    backups_dir = root / "backups" / project_slug / stamp
    backups_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = build_manifest_path(project_slug, home)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    installed_files: list[dict[str, Any]] = []
    for file_name, record in files.items():
        destination = agents_dir / file_name
        source_path = Path(record["path"])
        backup_path: str | None = None
        action = "created"
        if destination.exists():
            backup_target = backups_dir / file_name
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup_target)
            backup_path = str(backup_target)
            action = "overwritten"
        shutil.copy2(source_path, destination)
        installed_files.append(
            {
                "file_name": file_name,
                "role": record["role"],
                "target": target,
                "source_path": str(source_path),
                "destination_path": str(destination),
                "action": action,
                "backup_path": backup_path,
            }
        )

    home_field = "codex_home" if target == "codex" else "claude_home"
    manifest_payload = {
        "tool": "agents-team-builder",
        "action": "install",
        "target": target,
        "project_name": payload["request"]["project_name"],
        "project_slug": project_slug,
        "installed_at": stamp,
        home_field: str(home),
        "source_json": str(json_out),
        "installed_files": installed_files,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"action": "install", "target": target, "path": str(manifest_path)}


def install_team(payload: dict[str, Any], json_out: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    """Install to whichever targets are active. Returns one manifest descriptor
    per target so the payload can record both."""
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifests: list[dict[str, Any]] = []
    if args.target in ("codex", "both") and payload.get("toml_files"):
        manifests.append(
            _install_target_files(
                target="codex",
                home=resolve_codex_home(args),
                files=payload["toml_files"],
                payload=payload,
                json_out=json_out,
                stamp=stamp,
            )
        )
    if args.target in ("claude-code", "both") and payload.get("claude_code_files"):
        manifests.append(
            _install_target_files(
                target="claude-code",
                home=resolve_claude_home(args),
                files=payload["claude_code_files"],
                payload=payload,
                json_out=json_out,
                stamp=stamp,
            )
        )
    return manifests


def _uninstall_one_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored_files: list[dict[str, Any]] = []
    for item in manifest_payload.get("installed_files", []):
        destination = Path(item["destination_path"])
        backup_path = item.get("backup_path")
        if backup_path:
            backup = Path(backup_path)
            if backup.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, destination)
                backup.unlink()
                restored_files.append({"file_name": item["file_name"], "action": "restored-backup"})
            else:
                restored_files.append({"file_name": item["file_name"], "action": "missing-backup"})
        else:
            if destination.exists():
                destination.unlink()
            restored_files.append({"file_name": item["file_name"], "action": "removed-installed-file"})

    manifest_path.unlink(missing_ok=True)
    for directory in [manifest_path.parent, manifest_path.parent.parent]:
        try:
            directory.rmdir()
        except OSError:
            pass
    return {
        "tool": "agents-team-builder",
        "action": "uninstall",
        "target": manifest_payload.get("target", "codex"),
        "project_name": manifest_payload.get("project_name", ""),
        "project_slug": manifest_payload.get("project_slug", ""),
        "manifest_path": str(manifest_path),
        "restored_files": restored_files,
    }


def uninstall_team(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[Path]]:
    """Uninstall manifests for the requested target(s).

    With --manifest, only that single manifest is uninstalled regardless of
    target. With --project-name, look up manifests under whichever homes the
    --target flag selects; any missing manifest raises FileNotFoundError unless
    at least one target succeeds (so `--target both` tolerates a one-sided
    install)."""
    if args.manifest:
        report = _uninstall_one_manifest(Path(args.manifest))
        return [report], [Path(args.manifest)]

    project_slug = slugify(args.project_name)
    homes: list[tuple[str, Path]] = []
    if args.target in ("codex", "both"):
        homes.append(("codex", resolve_codex_home(args)))
    if args.target in ("claude-code", "both"):
        homes.append(("claude-code", resolve_claude_home(args)))

    reports: list[dict[str, Any]] = []
    paths: list[Path] = []
    errors: list[str] = []
    for target, home in homes:
        manifest_path = build_manifest_path(project_slug, home)
        try:
            reports.append(_uninstall_one_manifest(manifest_path))
            paths.append(manifest_path)
        except FileNotFoundError as exc:
            errors.append(f"{target}: {exc}")

    if not reports:
        # Nothing got uninstalled — surface every error so the caller can debug.
        raise FileNotFoundError("; ".join(errors) or f"No manifest found for {project_slug}")
    return reports, paths


def build_payload(args: argparse.Namespace) -> tuple[dict[str, Any], Path, Path]:
    input_path = Path(args.input)
    brief_text = load_text(input_path)
    project_name = args.project_name or input_path.stem
    project_slug = slugify(project_name)
    output_dir = ensure_output_dir(args, project_slug)
    json_out = Path(args.json_out) if args.json_out else output_dir / f"{project_slug}-agents-team.json"
    markdown_out = (
        Path(args.markdown_out) if args.markdown_out else output_dir / f"{project_slug}-agents-team.md"
    )

    workflow_profile, workflow_detection = detect_workflow_profile(brief_text, args.workflow_profile)
    workflow_steps = [dict(item) for item in WORKFLOW_STEPS[workflow_profile]]
    workflow_integrations = [dict(item) for item in WORKFLOW_INTEGRATIONS[workflow_profile]]

    tasks = detect_tasks(brief_text)
    parallel_groups = build_parallel_groups(tasks)
    agents = enrich_agents_for_profile(build_agents(tasks), workflow_profile)
    prompts = build_prompts(agents, tasks)
    assumptions = build_assumptions(input_path, args, tasks, workflow_profile)
    execution_plan = build_execution_plan(tasks)
    risks = build_risks(tasks, workflow_profile)
    open_questions = build_open_questions(tasks, workflow_profile, args.target)

    target = args.target
    toml_files: dict[str, dict[str, Any]] = {}
    if target in ("codex", "both"):
        toml_dir = output_dir / "toml-drafts"
        toml_dir.mkdir(parents=True, exist_ok=True)
        for agent in agents:
            file_name = f"{agent['name']}.toml"
            content = render_toml(agent)
            file_path = toml_dir / file_name
            file_path.write_text(content, encoding="utf-8")
            toml_files[file_name] = {"path": str(file_path), "role": agent["role"], "content": content}

    claude_code_files: dict[str, dict[str, Any]] = {}
    team_brief: dict[str, Any] = {}
    if target in ("claude-code", "both"):
        cc_dir = output_dir / "claude-agents"
        cc_dir.mkdir(parents=True, exist_ok=True)
        for agent in agents:
            cc_name = claude_code_agent_name(agent["name"])
            file_name = f"{cc_name}.md"
            content = render_claude_code_agent(agent)
            file_path = cc_dir / file_name
            file_path.write_text(content, encoding="utf-8")
            claude_code_files[file_name] = {
                "path": str(file_path),
                "role": agent["role"],
                "name": cc_name,
                "content": content,
            }

    payload = {
        "request": {
            "project_name": project_name,
            "project_slug": project_slug,
            "input_path": str(input_path),
            "source_summary": brief_text.strip(),
        },
        "target": target,
        "workflow_profile": workflow_profile,
        "workflow_detection": workflow_detection,
        "workflow_steps": workflow_steps,
        "workflow_integrations": workflow_integrations,
        "assumptions": assumptions,
        "task_graph": [task.to_payload() for task in tasks],
        "parallel_groups": parallel_groups,
        "agents": agents,
        "prompts": prompts,
        "toml_files": toml_files,
        "claude_code_files": claude_code_files,
        "team_brief": team_brief,
        "execution_plan": execution_plan,
        "risks": risks,
        "open_questions": open_questions,
        "install_manifest": {},
        "installed_files": [],
        "install_actions": [],
    }

    if target in ("claude-code", "both"):
        brief_path = output_dir / f"{project_slug}-claude-team-brief.md"
        brief_content = build_team_brief(payload)
        brief_path.write_text(brief_content, encoding="utf-8")
        payload["team_brief"] = {"path": str(brief_path), "content": brief_content}

    return payload, json_out, markdown_out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.uninstall:
        uninstall_reports, manifest_paths = uninstall_team(args)
        for manifest_path in manifest_paths:
            print(f"UNINSTALLED_MANIFEST={manifest_path}")
        print("UNINSTALL_OK=1")
        # Preserve the historical single-object stdout shape when only one manifest
        # is removed; emit a list when both targets were uninstalled together.
        body = uninstall_reports[0] if len(uninstall_reports) == 1 else uninstall_reports
        print(json.dumps(body, ensure_ascii=False))
        return 0

    payload, json_out, markdown_out = build_payload(args)

    if args.install:
        manifests = install_team(payload, json_out, args)
        # Backwards compatible shape: when only one manifest exists (typical
        # codex-only path), expose it as a dict so existing callers / tests
        # that read .install_manifest["path"] keep working.
        if len(manifests) == 1:
            payload["install_manifest"] = manifests[0]
            manifest_payload = json.loads(Path(manifests[0]["path"]).read_text(encoding="utf-8"))
            payload["installed_files"] = manifest_payload["installed_files"]
            payload["install_actions"] = [item["action"] for item in manifest_payload["installed_files"]]
        elif manifests:
            payload["install_manifest"] = manifests
            installed_files: list[dict[str, Any]] = []
            for manifest in manifests:
                manifest_payload = json.loads(Path(manifest["path"]).read_text(encoding="utf-8"))
                installed_files.extend(manifest_payload["installed_files"])
            payload["installed_files"] = installed_files
            payload["install_actions"] = [item["action"] for item in installed_files]

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_markdown(payload), encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    if payload.get("toml_files"):
        print(f"TOML_DIR={Path(next(iter(payload['toml_files'].values()))['path']).parent}")
    if payload.get("claude_code_files"):
        print(f"CLAUDE_AGENTS_DIR={Path(next(iter(payload['claude_code_files'].values()))['path']).parent}")
    if payload.get("team_brief"):
        print(f"TEAM_BRIEF={payload['team_brief']['path']}")
    if payload["install_manifest"]:
        manifest_field = payload["install_manifest"]
        if isinstance(manifest_field, list):
            for manifest in manifest_field:
                print(f"INSTALL_MANIFEST_{manifest['target'].upper().replace('-', '_')}={manifest['path']}")
        else:
            print(f"INSTALL_MANIFEST={manifest_field['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
