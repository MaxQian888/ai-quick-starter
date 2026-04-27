from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


def load_module(module_name: str, relative_script_path: str):
    script_path = Path(__file__).resolve().parents[1] / relative_script_path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


reconcile = load_module("openspec_reconcile_change_artifacts", "scripts/reconcile_change_artifacts.py")


class FakeCli:
    def __init__(self, repo_root: Path, change_names: list[str]) -> None:
        self.repo_root = repo_root
        self.change_names = change_names
        self.archived: list[str] = []

    def list_changes(self) -> list[dict[str, object]]:
        changes: list[dict[str, object]] = []
        for change_name in self.change_names:
            change_dir = self.repo_root / "openspec" / "changes" / change_name
            if not change_dir.exists():
                continue
            tasks = self._task_counts(change_dir / "tasks.md")
            changes.append(
                {
                    "name": change_name,
                    "completedTasks": tasks["completed"],
                    "totalTasks": tasks["total"],
                    "status": "complete" if tasks["total"] and tasks["completed"] == tasks["total"] else "no-tasks",
                    "lastModified": "2026-04-02T00:00:00.000Z",
                }
            )
        return changes

    def show_change(self, change_name: str) -> dict[str, object]:
        change_dir = self.repo_root / "openspec" / "changes" / change_name
        deltas = []
        for spec_path in sorted((change_dir / "specs").rglob("spec.md")) if (change_dir / "specs").exists() else []:
            text = spec_path.read_text(encoding="utf-8")
            requirement_count = text.count("### Requirement:")
            if requirement_count:
                deltas.append(
                    {
                        "spec": spec_path.parent.name,
                        "operation": "ADDED",
                        "description": f"{requirement_count} requirement blocks detected.",
                    }
                )
        return {"id": change_name, "title": change_name, "deltaCount": len(deltas), "deltas": deltas}

    def status(self, change_name: str) -> dict[str, object]:
        change_dir = self.repo_root / "openspec" / "changes" / change_name
        proposal = change_dir / "proposal.md"
        design = change_dir / "design.md"
        specs = change_dir / "specs"
        tasks = change_dir / "tasks.md"
        task_counts = self._task_counts(tasks)
        artifacts = [
            {"id": "proposal", "outputPath": "proposal.md", "status": "done" if proposal.exists() else "ready"},
            {"id": "design", "outputPath": "design.md", "status": "done" if design.exists() else "ready"},
            {
                "id": "specs",
                "outputPath": "specs/**/*.md",
                "status": "done" if specs.exists() and any(specs.rglob("*.md")) else "ready",
            },
            {
                "id": "tasks",
                "outputPath": "tasks.md",
                "status": "done" if tasks.exists() else "blocked",
                "missingDeps": [] if tasks.exists() else ["design", "specs"],
            },
        ]
        is_complete = all(item["status"] == "done" for item in artifacts) and (
            task_counts["total"] == 0 or task_counts["completed"] == task_counts["total"]
        )
        return {
            "changeName": change_name,
            "schemaName": "spec-driven",
            "isComplete": is_complete,
            "applyRequires": ["tasks"],
            "artifacts": artifacts,
        }

    def validate(self, change_name: str) -> dict[str, object]:
        change_dir = self.repo_root / "openspec" / "changes" / change_name
        issues: list[dict[str, str]] = []
        if not (change_dir / "design.md").exists():
            issues.append({"level": "ERROR", "message": "Missing design.md"})
        spec_files = list((change_dir / "specs").rglob("spec.md")) if (change_dir / "specs").exists() else []
        if not spec_files:
            issues.append({"level": "ERROR", "message": "Missing delta specs"})
        for spec_path in spec_files:
            text = spec_path.read_text(encoding="utf-8")
            if "#### Scenario:" not in text:
                issues.append({"level": "ERROR", "message": f"Missing scenario blocks in {spec_path.name}"})
        if not (change_dir / "tasks.md").exists():
            issues.append({"level": "ERROR", "message": "Missing tasks.md"})
        return {
            "items": [
                {
                    "id": change_name,
                    "type": "change",
                    "valid": not issues,
                    "issues": issues,
                }
            ]
        }

    def archive(self, change_name: str) -> str:
        change_dir = self.repo_root / "openspec" / "changes" / change_name
        archive_dir = self.repo_root / "openspec" / "changes" / "archive" / f"archived-{change_name}"
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(change_dir), str(archive_dir))
        main_spec_dir = self.repo_root / "openspec" / "specs"
        for spec_path in archive_dir.rglob("spec.md"):
            target = main_spec_dir / spec_path.parent.name / "spec.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            source_text = spec_path.read_text(encoding="utf-8")
            requirement_body = source_text.split("## ADDED Requirements", 1)[1].lstrip() if "## ADDED Requirements" in source_text else ""
            target.write_text(
                (
                    f"# {spec_path.parent.name} Specification\n\n"
                    "## Purpose\n"
                    f"TBD - created by archiving change {change_name}. Update Purpose after archive.\n"
                    "## Requirements\n"
                    f"{requirement_body}"
                ),
                encoding="utf-8",
            )
        self.archived.append(change_name)
        return f"archived {change_name}"

    def _task_counts(self, tasks_path: Path) -> dict[str, int]:
        if not tasks_path.exists():
            return {"total": 0, "completed": 0}
        total = 0
        completed = 0
        for line in tasks_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("- ["):
                total += 1
                if stripped.startswith("- [x]") or stripped.startswith("- [X]"):
                    completed += 1
        return {"total": total, "completed": completed}


class ReconcileChangeArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="openspec-reconcile-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir)

    def make_file(self, relative_path: str, content: str) -> None:
        file_path = self.tmpdir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    def make_skill_module(self, skill_name: str) -> None:
        self.make_file(
            f"{skill_name}/SKILL.md",
            (
                f"---\nname: {skill_name}\n"
                "description: Use when Codex needs deterministic repo navigation help.\n---\n\n"
                f"# {skill_name.title()}\n\n"
                "Generate a repository report before broad file reads.\n"
            ),
        )
        self.make_file(
            f"{skill_name}/CLAUDE.md",
            (
                "# CLAUDE.md\n\n"
                "## Purpose\n\n"
                f"`{skill_name}` builds temporary repository maps for onboarding.\n\n"
                "## Main Interface\n\n"
                "- `python scripts/build_report.py --root <repo>`\n\n"
                "## Output Contract\n\n"
                "- Markdown report\n"
                "- JSON index\n"
            ),
        )
        self.make_file(
            f"{skill_name}/agents/openai.yaml",
            (
                "interface:\n"
                f"  display_name: \"{skill_name.title()}\"\n"
                "  short_description: \"Build repo maps\"\n"
                f"  default_prompt: \"Use ${skill_name} to inspect this repository.\"\n"
            ),
        )
        self.make_file(f"{skill_name}/references/output-schema.md", "# Output Schema\n\n- Markdown report\n- JSON index\n")
        self.make_file(f"{skill_name}/scripts/build_report.py", "print('ok')\n")
        self.make_file(f"{skill_name}/tests/test_build_report.py", "def test_ok():\n    assert True\n")

    def make_change(self, change_name: str, skill_name: str, capability_name: str) -> None:
        self.make_file(
            f"openspec/changes/{change_name}/proposal.md",
            (
                "## Why\n\n"
                "Need to backfill missing OpenSpec artifacts.\n\n"
                "## What Changes\n\n"
                f"- Document the existing `{skill_name}` module.\n\n"
                "## Capabilities\n\n"
                "### New Capabilities\n"
                f"- `{capability_name}`: Build repository maps and reading guidance.\n\n"
                "### Modified Capabilities\n"
                "- None.\n"
            ),
        )
        self.make_file(f"openspec/changes/{change_name}/.openspec.yaml", "schema: spec-driven\n")

    def test_reconcile_backfills_missing_artifacts_from_module_evidence(self) -> None:
        self.make_skill_module("demo-index-skill")
        self.make_change("create-demo-index-skill", "demo-index-skill", "demo-indexing")
        cli = FakeCli(self.tmpdir, ["create-demo-index-skill"])

        result = reconcile.reconcile_changes(
            repo_root=self.tmpdir,
            cli=cli,
            change_names=["create-demo-index-skill"],
            archive_when_ready=False,
        )

        change_dir = self.tmpdir / "openspec" / "changes" / "create-demo-index-skill"
        self.assertTrue((change_dir / "design.md").exists())
        self.assertTrue((change_dir / "tasks.md").exists())
        self.assertTrue((change_dir / "specs" / "demo-indexing" / "spec.md").exists())
        self.assertIn("create-demo-index-skill", result["summary"]["repaired_changes"])
        self.assertEqual(cli.archived, [])

    def test_reconcile_archives_when_repaired_change_becomes_complete(self) -> None:
        self.make_skill_module("demo-index-skill")
        self.make_change("create-demo-index-skill", "demo-index-skill", "demo-indexing")
        cli = FakeCli(self.tmpdir, ["create-demo-index-skill"])

        result = reconcile.reconcile_changes(
            repo_root=self.tmpdir,
            cli=cli,
            change_names=["create-demo-index-skill"],
            archive_when_ready=True,
        )

        self.assertIn("create-demo-index-skill", cli.archived)
        self.assertFalse((self.tmpdir / "openspec" / "changes" / "create-demo-index-skill").exists())
        self.assertTrue((self.tmpdir / "openspec" / "specs" / "demo-indexing" / "spec.md").exists())
        main_spec = (self.tmpdir / "openspec" / "specs" / "demo-indexing" / "spec.md").read_text(encoding="utf-8")
        self.assertNotIn("Update Purpose after archive", main_spec)
        self.assertIn("create-demo-index-skill", result["summary"]["archived_changes"])

    def test_reconcile_blocks_when_module_cannot_be_inferred(self) -> None:
        self.make_change("create-unknown-skill", "missing-skill", "unknown-capability")
        proposal_path = self.tmpdir / "openspec" / "changes" / "create-unknown-skill" / "proposal.md"
        proposal_path.write_text(
            proposal_path.read_text(encoding="utf-8").replace("`missing-skill`", "`nonexistent-module`"),
            encoding="utf-8",
        )
        cli = FakeCli(self.tmpdir, ["create-unknown-skill"])

        result = reconcile.reconcile_changes(
            repo_root=self.tmpdir,
            cli=cli,
            change_names=["create-unknown-skill"],
            archive_when_ready=False,
        )

        self.assertIn("create-unknown-skill", result["summary"]["blocked_changes"])
        self.assertFalse(
            (self.tmpdir / "openspec" / "changes" / "create-unknown-skill" / "design.md").exists()
        )


if __name__ == "__main__":
    unittest.main()
