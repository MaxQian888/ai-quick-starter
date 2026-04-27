from __future__ import annotations

import json
import subprocess
import shutil
import uuid
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
TMP_ROOT = WORKSPACE_ROOT / "development-task-orchestrator" / ".tmp-tests"
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "development-task-orchestrator" / "scripts" / "build_execution_orchestration.py"


class BuildExecutionOrchestrationTests(unittest.TestCase):
    def make_case_dir(self, prefix: str) -> Path:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        case_dir = TMP_ROOT / f"{prefix}-{uuid.uuid4().hex}"
        if case_dir.exists():
            shutil.rmtree(case_dir)
        case_dir.mkdir(parents=True, exist_ok=True)
        return case_dir

    def make_input(self, content: str) -> Path:
        case_dir = self.make_case_dir("input")
        input_path = case_dir / "input.md"
        input_path.write_text(content, encoding="utf-8")
        return input_path

    def make_output_dir(self) -> Path:
        return self.make_case_dir("output")

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [str(PYTHON), str(SCRIPT), *args]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def load_json_from_stdout(self, stdout: str) -> dict[str, object]:
        json_path = self.read_output_path(stdout, "JSON_OUT")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def test_normalizes_checklist_input_into_work_items(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "# Implementation checklist",
                    "- [ ] Finalize API contract (writes: src/api/contracts.ts)",
                    "- [ ] Implement backend handler after Finalize API contract (writes: src/server/handler.ts)",
                    "- [ ] Wire settings page after Implement backend handler (writes: src/app/settings/page.tsx)",
                    "- [ ] Add integration test after Wire settings page (writes: tests/settings-flow.test.ts)",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--format", "checklist", "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        titles = {item["title"] for item in payload["work_items"]}
        self.assertIn("Finalize API Contract", titles)
        self.assertIn("Implement Backend Handler", titles)
        self.assertIn("Wire Settings Page", titles)
        self.assertIn("Add Integration Test", titles)
        dependency_pairs = {(item["from"], item["to"]) for item in payload["dependencies"]}
        self.assertTrue(any(pair[1].endswith("implement-backend-handler") for pair in dependency_pairs))

    def test_prevents_same_batch_write_scope_conflicts(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "# Tasks",
                    "- [ ] Update dashboard page copy (writes: src/app/dashboard/page.tsx)",
                    "- [ ] Refactor dashboard page loading state (writes: src/app/dashboard/page.tsx)",
                    "- [ ] Draft release notes (writes: docs/dashboard-release.md)",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--format", "tasks", "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        batches = payload["parallel_batches"]
        conflicting_ids = {
            item["id"]
            for item in payload["work_items"]
            if item["title"] in {"Update Dashboard Page Copy", "Refactor Dashboard Page Loading State"}
        }
        for batch in batches:
            self.assertLess(len(conflicting_ids.intersection(set(batch["tasks"]))), 2)

    def test_renders_markdown_and_json_contract_outputs(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "# Execution plan",
                    "- [ ] Add save button wiring (writes: src/app/settings/page.tsx)",
                    "- [ ] Add server mutation (writes: src/server/settings.ts)",
                    "- [ ] Add regression test after Add save button wiring (writes: tests/settings-page.test.ts)",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--format", "auto", "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertEqual(
            sorted(payload.keys()),
            sorted(
                [
                    "assumptions",
                    "blocked_items",
                    "checkpoint_sequence",
                    "dependencies",
                    "input_summary",
                    "main_thread_duties",
                    "merge_points",
                    "parallel_batches",
                    "risks",
                    "verification_boundaries",
                    "work_items",
                ]
            ),
        )

        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Input Summary", markdown)
        self.assertIn("## Parallel Batches", markdown)
        self.assertIn("## Main-Thread Duties", markdown)
        self.assertIn("## Verification Boundaries", markdown)

    def test_respects_explicit_output_paths(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "- [ ] Draft API checklist (writes: docs/api-checklist.md)",
                    "- [ ] Implement API route after Draft API checklist (writes: src/api/route.ts)",
                ]
            )
        )
        output_dir = self.make_output_dir()
        json_out = output_dir / "nested" / "plan.json"
        markdown_out = output_dir / "reports" / "plan.md"

        result = self.run_cli(
            "--input",
            str(input_path),
            "--format",
            "auto",
            "--output-dir",
            str(output_dir),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(json_out.exists(), str(json_out))
        self.assertTrue(markdown_out.exists(), str(markdown_out))
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(payload["input_summary"]["source_path"], str(input_path))
        markdown = markdown_out.read_text(encoding="utf-8")
        self.assertIn("## Execution Units", markdown)

    def test_auto_format_extracts_plain_task_lines_and_blocked_items(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "Build execution brief",
                    "- Prepare migration summary (writes: docs/migration.md)",
                    "- Update API endpoint after Prepare migration summary (writes: src/api/endpoint.ts)",
                    "- Refresh dashboard copy after Update API endpoint (writes: src/app/dashboard/page.tsx)",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--format", "auto", "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        titles = [item["title"] for item in payload["work_items"]]
        self.assertIn("Prepare Migration Summary", titles)
        self.assertIn("Update API Endpoint", titles)
        self.assertIn("Refresh Dashboard Copy", titles)
        blocked_ids = {item["id"] for item in payload["blocked_items"]}
        self.assertIn("update-api-endpoint", blocked_ids)
        self.assertIn("refresh-dashboard-copy", blocked_ids)

    def test_same_write_scope_with_slash_variants_stays_serialized(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "# Tasks",
                    r"- [ ] Update settings page copy (writes: src/app/settings/page.tsx)",
                    r"- [ ] Refactor settings page loading state (writes: src\app\settings\page.tsx)",
                    r"- [ ] Draft release note (writes: docs/settings.md)",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--format", "tasks", "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        conflicting_ids = {
            item["id"]
            for item in payload["work_items"]
            if item["title"] in {"Update Settings Page Copy", "Refactor Settings Page Loading State"}
        }
        for batch in payload["parallel_batches"]:
            self.assertLess(len(conflicting_ids.intersection(set(batch["tasks"]))), 2)

    def test_unspecified_write_scope_is_not_batched_with_write_heavy_tasks(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "# Tasks",
                    "- [ ] Investigate flaky test failure",
                    "- [ ] Update settings route (writes: src/api/settings/route.ts)",
                    "- [ ] Draft release note (writes: docs/settings.md)",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--format", "tasks", "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        investigate_id = next(
            item["id"] for item in payload["work_items"] if item["title"] == "Investigate Flaky Test Failure"
        )
        for batch in payload["parallel_batches"]:
            if investigate_id in set(batch["tasks"]):
                self.assertEqual(len(batch["tasks"]), 1)


if __name__ == "__main__":
    unittest.main()
