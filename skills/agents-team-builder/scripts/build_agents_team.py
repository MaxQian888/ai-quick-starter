#!/usr/bin/env python3
"""Build a Codex subagent team plan from a project brief."""

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
    parser.add_argument("--codex-home", default="", help="Override Codex home directory. Defaults to ~/.codex.")
    parser.add_argument("--install", action="store_true", help="Install generated agent TOML drafts into Codex.")
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
    assumptions = [
        f"Used {input_path.name} as the primary request source.",
        "This first-pass plan uses keyword heuristics instead of a semantic dependency graph.",
        (
            "Generated .toml files are reviewable drafts and are not installed automatically."
            if not args.install
            else "Install mode was explicitly requested, so generated .toml drafts were copied into the target Codex agents directory."
        ),
    ]
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


def build_open_questions(tasks: list[Task], workflow_profile: str) -> list[str]:
    questions = [
        "Should any custom agents be promoted from drafts into persistent ~/.codex/agents/*.toml files?",
        "Are there repository-specific instructions that should be merged into developer_instructions?",
    ]
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
    lines.append("## TOML Drafts")
    lines.append("")
    for file_name, record in payload["toml_files"].items():
        lines.append(f"### {file_name}")
        lines.append("")
        lines.append("```toml")
        lines.append(record["content"].rstrip())
        lines.append("```")
        lines.append("")
    if payload["install_manifest"]:
        lines.append("## Install Management")
        lines.append("")
        lines.append(f"- Manifest: `{payload['install_manifest']['path']}`")
        for item in payload["installed_files"]:
            detail = item["action"]
            if item.get("backup_path"):
                detail += f", backup: {item['backup_path']}"
            lines.append(f"- `{item['file_name']}` -> `{item['destination_path']}` ({detail})")
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


def manifest_root(codex_home: Path) -> Path:
    return codex_home / "agents" / ".agents-team-builder"


def build_manifest_path(project_slug: str, codex_home: Path) -> Path:
    return manifest_root(codex_home) / "manifests" / f"{project_slug}.json"


def install_team(payload: dict[str, Any], json_out: Path, args: argparse.Namespace) -> dict[str, Any]:
    codex_home = resolve_codex_home(args)
    agents_dir = codex_home / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    project_slug = payload["request"]["project_slug"]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = manifest_root(codex_home)
    backups_dir = root / "backups" / project_slug / stamp
    backups_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = build_manifest_path(project_slug, codex_home)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    installed_files: list[dict[str, Any]] = []
    for file_name, record in payload["toml_files"].items():
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
                "source_path": str(source_path),
                "destination_path": str(destination),
                "action": action,
                "backup_path": backup_path,
            }
        )

    manifest_payload = {
        "tool": "agents-team-builder",
        "action": "install",
        "project_name": payload["request"]["project_name"],
        "project_slug": project_slug,
        "installed_at": stamp,
        "codex_home": str(codex_home),
        "source_json": str(json_out),
        "installed_files": installed_files,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"action": "install", "path": str(manifest_path)}


def uninstall_team(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    codex_home = resolve_codex_home(args)
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        manifest_path = build_manifest_path(slugify(args.project_name), codex_home)
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
    report = {
        "tool": "agents-team-builder",
        "action": "uninstall",
        "project_name": manifest_payload.get("project_name", ""),
        "project_slug": manifest_payload.get("project_slug", ""),
        "manifest_path": str(manifest_path),
        "restored_files": restored_files,
    }
    return report, manifest_path


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
    open_questions = build_open_questions(tasks, workflow_profile)

    toml_dir = output_dir / "toml-drafts"
    toml_dir.mkdir(parents=True, exist_ok=True)
    toml_files: dict[str, dict[str, Any]] = {}
    for agent in agents:
        file_name = f"{agent['name']}.toml"
        content = render_toml(agent)
        file_path = toml_dir / file_name
        file_path.write_text(content, encoding="utf-8")
        toml_files[file_name] = {"path": str(file_path), "role": agent["role"], "content": content}

    payload = {
        "request": {
            "project_name": project_name,
            "project_slug": project_slug,
            "input_path": str(input_path),
            "source_summary": brief_text.strip(),
        },
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
        "execution_plan": execution_plan,
        "risks": risks,
        "open_questions": open_questions,
        "install_manifest": {},
        "installed_files": [],
        "install_actions": [],
    }
    return payload, json_out, markdown_out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.uninstall:
        uninstall_payload, manifest_path = uninstall_team(args)
        print(f"UNINSTALLED_MANIFEST={manifest_path}")
        print("UNINSTALL_OK=1")
        print(json.dumps(uninstall_payload, ensure_ascii=False))
        return 0

    payload, json_out, markdown_out = build_payload(args)

    if args.install:
        manifest = install_team(payload, json_out, args)
        payload["install_manifest"] = manifest
        manifest_payload = json.loads(Path(manifest["path"]).read_text(encoding="utf-8"))
        payload["installed_files"] = manifest_payload["installed_files"]
        payload["install_actions"] = [item["action"] for item in manifest_payload["installed_files"]]

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(render_markdown(payload), encoding="utf-8")

    print(f"MARKDOWN_OUT={markdown_out}")
    print(f"JSON_OUT={json_out}")
    print(f"TOML_DIR={Path(next(iter(payload['toml_files'].values()))['path']).parent}")
    if payload["install_manifest"]:
        print(f"INSTALL_MANIFEST={payload['install_manifest']['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
