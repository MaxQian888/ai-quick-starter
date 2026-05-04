#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


SUPPORTED_USES_PREFIXES = (
    "actions/checkout@",
    "actions/setup-",
    "actions/cache@",
    "pnpm/action-setup@",
    "ruby/setup-ruby@",
    "actions/upload-artifact@",
    "actions/download-artifact@",
)

BLOCK_SCALAR_TOKENS = {"|", "|-", ">", ">-"}

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
)


@dataclass
class WorkflowStep:
    kind: str
    name: str
    value: str
    working_directory: str = ""


@dataclass
class WorkflowJob:
    id: str
    name: str
    steps: list[WorkflowStep] = field(default_factory=list)
    working_directory: str = ""


@dataclass
class WorkflowRecord:
    path: str
    name: str
    jobs: list[WorkflowJob] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    selected_mode: str
    runnable_commands: list[str]
    skipped_steps: list[WorkflowStep]
    blockers: list[str]
    overall_status: str
    runnable_steps: list[WorkflowStep] = field(default_factory=list)


@dataclass
class CommandResult:
    command: str
    returncode: int
    status: str
    stdout: str
    stderr: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect GitHub Actions workflows and build a local CI execution plan."
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--workflow")
    parser.add_argument("--job")
    parser.add_argument("--mode", choices=("auto", "act", "fallback"), default="auto")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--max-output-chars", type=int, default=12000)
    return parser.parse_args(argv)


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_scalar(text: str) -> str:
    return strip_quotes(text.split(":", 1)[1].strip())


def truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n...[truncated]..."


def parse_step_line(current_step: WorkflowStep, stripped: str) -> tuple[WorkflowStep, bool]:
    if stripped.startswith("name:"):
        current_step.name = parse_scalar(stripped)
        return current_step, False
    if stripped.startswith("run:"):
        current_step.kind = "run"
        current_step.value = parse_scalar(stripped)
        return current_step, True
    if stripped.startswith("uses:"):
        current_step.kind = "uses"
        current_step.value = parse_scalar(stripped)
        return current_step, True
    if stripped.startswith("working-directory:"):
        current_step.working_directory = parse_scalar(stripped)
        return current_step, False
    return current_step, False


def parse_block_scalar_token(stripped: str, field_name: str) -> str | None:
    if not stripped.startswith(f"{field_name}:"):
        return None
    value = stripped.split(":", 1)[1].strip()
    if value in BLOCK_SCALAR_TOKENS:
        return value
    return None


def finalize_step(job: WorkflowJob | None, current_step: WorkflowStep | None) -> WorkflowStep | None:
    if job is not None and current_step is not None and current_step.kind and current_step.value:
        job.steps.append(current_step)
    return None


def discover_workflows(root: Path) -> list[WorkflowRecord]:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return []

    workflows: list[WorkflowRecord] = []
    for path in sorted(workflow_dir.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        workflow = WorkflowRecord(path=str(path), name=path.stem)
        current_job: WorkflowJob | None = None
        current_step: WorkflowStep | None = None
        in_jobs = False
        in_steps = False
        # The indent at which a step's properties (run:, uses:, name:, ...) live.
        # Computed when we encounter the step's "- " marker so we can ignore
        # deeper-nested mappings (env:, with:) whose keys may collide with
        # step property names.
        step_property_indent: int | None = None
        multiline_parent_indent: int | None = None
        multiline_content_indent: int | None = None
        multiline_lines: list[str] = []

        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            indent = len(raw_line) - len(raw_line.lstrip(" "))

            if multiline_parent_indent is not None and current_step is not None:
                if stripped == "" and multiline_content_indent is not None and indent >= multiline_content_indent:
                    multiline_lines.append("")
                    continue
                if indent > multiline_parent_indent:
                    if multiline_content_indent is None and stripped:
                        multiline_content_indent = indent
                    if multiline_content_indent is None:
                        multiline_lines.append("")
                    else:
                        multiline_lines.append(raw_line[multiline_content_indent:])
                    continue

                current_step.value = "\n".join(multiline_lines).rstrip()
                multiline_parent_indent = None
                multiline_content_indent = None
                multiline_lines = []

            if not stripped or stripped.startswith("#"):
                continue

            if indent == 0 and stripped.startswith("name:"):
                workflow.name = parse_scalar(stripped)
                continue

            if indent == 0 and stripped == "jobs:":
                in_jobs = True
                continue

            if not in_jobs:
                continue

            if indent == 2 and stripped.endswith(":") and not stripped.startswith(("name:", "env:", "defaults:")):
                current_step = finalize_step(current_job, current_step)
                step_property_indent = None
                current_job = WorkflowJob(id=stripped[:-1], name=stripped[:-1])
                workflow.jobs.append(current_job)
                in_steps = False
                continue

            if current_job is None:
                continue

            if indent == 4 and stripped.startswith("name:"):
                current_job.name = parse_scalar(stripped)
                continue

            if indent == 4 and stripped.startswith("working-directory:"):
                current_job.working_directory = parse_scalar(stripped)
                continue

            if indent == 4 and stripped == "steps:":
                in_steps = True
                continue

            if not in_steps:
                continue

            if indent == 6 and stripped.startswith("- "):
                current_step = finalize_step(current_job, current_step)
                current_step = WorkflowStep(kind="", name="", value="", working_directory=current_job.working_directory)
                step_property_indent = indent + 2
                step_line = stripped[2:].strip()
                if parse_block_scalar_token(step_line, "run") is not None:
                    current_step.kind = "run"
                    multiline_parent_indent = step_property_indent
                    multiline_content_indent = None
                    multiline_lines = []
                    continue
                current_step, _complete = parse_step_line(current_step, step_line)
                continue

            if current_step is not None and step_property_indent is not None and indent == step_property_indent:
                if parse_block_scalar_token(stripped, "run") is not None:
                    current_step.kind = "run"
                    multiline_parent_indent = indent
                    multiline_content_indent = None
                    multiline_lines = []
                    continue
                current_step, _complete = parse_step_line(current_step, stripped)
                continue

            if current_step is not None and step_property_indent is not None and indent > step_property_indent:
                # Inside a nested mapping (env:, with:, etc.) — keys here are
                # not step properties even if they share names like `name:`.
                continue

            if indent <= 4:
                current_step = finalize_step(current_job, current_step)
                step_property_indent = None
                in_steps = False

        if multiline_parent_indent is not None and current_step is not None:
            current_step.value = "\n".join(multiline_lines).rstrip()
        finalize_step(current_job, current_step)
        workflows.append(workflow)

    return workflows


def tool_exists(name: str) -> bool:
    return shutil.which(name) is not None


def inspect_environment() -> dict[str, bool]:
    return {
        "act": tool_exists("act"),
        "docker": tool_exists("docker"),
        "git": tool_exists("git"),
    }


def is_supported_use(value: str) -> bool:
    lowered = value.lower()
    return any(lowered.startswith(prefix) for prefix in SUPPORTED_USES_PREFIXES)


def has_keyword(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def matches_workflow(workflow: WorkflowRecord, workflow_filter: str | None) -> bool:
    if not workflow_filter:
        return True
    lowered = workflow_filter.lower()
    return lowered in Path(workflow.path).name.lower() or lowered == workflow.name.lower()


def matches_job(job: WorkflowJob, job_filter: str | None) -> bool:
    if not job_filter:
        return True
    lowered = job_filter.lower()
    return lowered == job.id.lower() or lowered == job.name.lower()


def build_execution_plan(
    workflows: list[WorkflowRecord],
    environment: dict[str, bool],
    requested_mode: str,
    workflow_filter: str | None = None,
    job_filter: str | None = None,
) -> ExecutionPlan:
    if not workflows:
        return ExecutionPlan(
            selected_mode="unsupported",
            runnable_commands=[],
            runnable_steps=[],
            skipped_steps=[],
            blockers=["No GitHub Actions workflows found under .github/workflows."],
            overall_status="blocked",
        )

    filtered_workflows = [workflow for workflow in workflows if matches_workflow(workflow, workflow_filter)]
    runnable_commands: list[str] = []
    runnable_steps: list[WorkflowStep] = []
    skipped_steps: list[WorkflowStep] = []
    blockers: list[str] = []
    has_validation_signal = False
    has_deploy_signal = False

    for workflow in filtered_workflows:
        has_deploy_signal = has_deploy_signal or has_keyword(workflow.name, DEPLOY_KEYWORDS)
        for job in workflow.jobs:
            if not matches_job(job, job_filter):
                continue
            has_deploy_signal = has_deploy_signal or has_keyword(job.id, DEPLOY_KEYWORDS) or has_keyword(job.name, DEPLOY_KEYWORDS)
            for step in job.steps:
                if step.kind == "run":
                    runnable_commands.append(step.value)
                    runnable_steps.append(step)
                    has_validation_signal = has_validation_signal or has_keyword(step.value, VALIDATION_KEYWORDS)
                    has_deploy_signal = has_deploy_signal or has_keyword(step.value, DEPLOY_KEYWORDS)
                elif step.kind == "uses":
                    if is_supported_use(step.value):
                        skipped_steps.append(step)
                    else:
                        skipped_steps.append(step)
                        blockers.append(f"Unsupported uses step requires manual review: {step.value}")

    if not filtered_workflows:
        return ExecutionPlan(
            selected_mode="unsupported",
            runnable_commands=[],
            runnable_steps=[],
            skipped_steps=[],
            blockers=["No workflows matched the requested filter."],
            overall_status="blocked",
        )

    if has_deploy_signal and not has_validation_signal:
        blockers.insert(0, "Deploy-only workflow cannot be safely simulated locally in version one.")
        return ExecutionPlan(
            selected_mode="unsupported",
            runnable_commands=runnable_commands,
            skipped_steps=skipped_steps,
            blockers=blockers,
            overall_status="blocked",
        )

    selected_mode = requested_mode
    if selected_mode == "auto":
        if environment["act"] and environment["docker"]:
            selected_mode = "act"
        elif runnable_commands:
            selected_mode = "fallback"
        else:
            selected_mode = "unsupported"

    if selected_mode == "act" and not (environment["act"] and environment["docker"]):
        blockers.append("Requested act mode but act or Docker is unavailable.")
        selected_mode = "unsupported"

    if selected_mode == "fallback" and not runnable_commands:
        blockers.append("Requested fallback mode but no reproducible run commands were found.")
        selected_mode = "unsupported"

    overall_status = "planned"
    if blockers and selected_mode != "unsupported":
        overall_status = "partial"
    if selected_mode == "unsupported":
        overall_status = "blocked"

    return ExecutionPlan(
        selected_mode=selected_mode,
        runnable_commands=runnable_commands,
        runnable_steps=runnable_steps,
        skipped_steps=skipped_steps,
        blockers=blockers,
        overall_status=overall_status,
    )


def run_command(root: Path, command: str, max_output_chars: int, working_directory: str = "") -> CommandResult:
    cwd = root
    if working_directory:
        cwd = (root / working_directory).resolve()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        stderr = str(exc)
        if working_directory:
            stderr += f"\nrequested-working-directory={working_directory}"
        stderr += f"\nworking-directory={cwd}"
        return CommandResult(
            command=command,
            returncode=1,
            status="failed",
            stdout="",
            stderr=truncate_text(stderr, max_output_chars),
        )
    status = "passed" if completed.returncode == 0 else "failed"
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        status=status,
        stdout=truncate_text(completed.stdout, max_output_chars),
        stderr=truncate_text(completed.stderr, max_output_chars),
    )


def run_fallback_plan(root: Path, steps: list[WorkflowStep], max_output_chars: int, fail_fast: bool) -> list[CommandResult]:
    results: list[CommandResult] = []
    for step in steps:
        result = run_command(
            root=root,
            command=step.value,
            max_output_chars=max_output_chars,
            working_directory=step.working_directory,
        )
        results.append(result)
        if fail_fast and result.status == "failed":
            break
    return results


def run_act_plan(
    root: Path,
    workflows: list[WorkflowRecord],
    workflow_filter: str | None,
    job_filter: str | None,
    max_output_chars: int,
) -> list[CommandResult]:
    matching = [workflow for workflow in workflows if matches_workflow(workflow, workflow_filter)]
    if not matching:
        return [
            CommandResult(
                command="act",
                returncode=1,
                status="failed",
                stdout="",
                stderr="No matching workflow found for act execution.",
            )
        ]

    command_parts = ["act", "-W", matching[0].path]
    if job_filter:
        command_parts.extend(["-j", job_filter])
    command = " ".join(command_parts)
    return [run_command(root=root, command=command, max_output_chars=max_output_chars)]


def derive_execution_status(plan: ExecutionPlan, results: list[CommandResult]) -> str:
    if plan.selected_mode == "unsupported":
        return "blocked"
    if any(result.status == "failed" for result in results):
        return "failed"
    if plan.blockers:
        return "partial"
    if results:
        return "passed"
    return plan.overall_status


def make_payload(
    root: Path,
    workflows: list[WorkflowRecord],
    environment: dict[str, bool],
    plan: ExecutionPlan,
    results: list[CommandResult],
    overall_status: str,
) -> dict[str, object]:
    return {
        "project_root": str(root),
        "workflow_count": len(workflows),
        "workflows": [asdict(workflow) for workflow in workflows],
        "environment": environment,
        "selected_mode": plan.selected_mode,
        "runnable_commands": plan.runnable_commands,
        "skipped_steps": [asdict(step) for step in plan.skipped_steps],
        "blockers": plan.blockers,
        "results": [asdict(result) for result in results],
        "overall_status": overall_status,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"Project root does not exist: {root}", file=sys.stderr)
        return 2

    workflows = discover_workflows(root)
    environment = inspect_environment()
    plan = build_execution_plan(
        workflows=workflows,
        environment=environment,
        requested_mode=args.mode,
        workflow_filter=args.workflow,
        job_filter=args.job,
    )

    if args.discover_only or args.plan_only:
        payload = make_payload(root, workflows, environment, plan, results=[], overall_status=plan.overall_status)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    results: list[CommandResult] = []
    if plan.selected_mode == "fallback":
        results = run_fallback_plan(
            root=root,
            steps=plan.runnable_steps,
            max_output_chars=args.max_output_chars,
            fail_fast=args.fail_fast,
        )
    elif plan.selected_mode == "act":
        results = run_act_plan(
            root=root,
            workflows=workflows,
            workflow_filter=args.workflow,
            job_filter=args.job,
            max_output_chars=args.max_output_chars,
        )

    overall_status = derive_execution_status(plan, results)
    payload = make_payload(root, workflows, environment, plan, results=results, overall_status=overall_status)

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Selected mode: {plan.selected_mode}")
        for command in plan.runnable_commands:
            print(f"- {command}")
        if results:
            print("Results:")
            for result in results:
                print(f"- {result.status.upper()} {result.command}")
        if plan.blockers:
            print("Blockers:")
            for blocker in plan.blockers:
                print(f"- {blocker}")

    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
