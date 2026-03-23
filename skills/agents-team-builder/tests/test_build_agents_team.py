from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "agents-team-builder" / "scripts" / "build_agents_team.py"


class BuildAgentsTeamTests(unittest.TestCase):
    def make_input(self, content: str) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="agents-team-builder-"))
        input_path = temp_dir / "brief.md"
        input_path.write_text(content, encoding="utf-8")
        return input_path

    def make_output_dir(self) -> Path:
        return Path(tempfile.mkdtemp(prefix="agents-team-output-"))

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

    def make_codex_home(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="codex-home-"))
        codex_home = root / ".codex"
        codex_home.mkdir(parents=True, exist_ok=True)
        return codex_home

    def test_decomposes_multisurface_project_into_expected_tasks(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "# Project brief",
                    "- write product documentation",
                    "- build database schema",
                    "- collect seed data from public sites",
                    "- write frontend pages",
                    "- write backend APIs",
                    "- debug integration issues",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli(
            "--input",
            str(input_path),
            "--project-name",
            "parallel-shop",
            "--output-dir",
            str(output_dir),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        task_titles = {item["title"] for item in payload["task_graph"]}
        self.assertIn("Documentation", task_titles)
        self.assertIn("Database", task_titles)
        self.assertIn("Data Collection", task_titles)
        self.assertIn("Frontend", task_titles)
        self.assertIn("Backend", task_titles)
        self.assertIn("Debugging", task_titles)

    def test_parallel_groups_keep_read_and_write_tracks_separate(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "Need docs, schema, frontend, backend, and debugging.",
                    "Research current competitors first, then build the app.",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertTrue(payload["parallel_groups"])
        group_task_ids = {task_id for group in payload["parallel_groups"] for task_id in group["tasks"]}
        self.assertTrue(group_task_ids)
        agent_roles = {agent["name"]: agent["role"] for agent in payload["agents"]}
        self.assertIn("explorer", agent_roles)
        self.assertIn("worker", agent_roles)

    def test_renders_toml_drafts_and_markdown_report(self) -> None:
        input_path = self.make_input(
            "Create docs, frontend, backend, and testing plans for a new web app."
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertIn("default.toml", payload["toml_files"])
        self.assertIn("worker.toml", payload["toml_files"])
        self.assertIn("explorer.toml", payload["toml_files"])

        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Agent Team", markdown)
        self.assertIn("## TOML Drafts", markdown)
        self.assertIn("## Risks And Guardrails", markdown)

    def test_existing_config_context_is_recorded_in_assumptions(self) -> None:
        input_path = self.make_input("Write docs and backend for a project with existing subagent config.")
        output_dir = self.make_output_dir()
        config_path = output_dir / "config.toml"
        config_path.write_text("[features]\nmulti_agent = true\n", encoding="utf-8")

        result = self.run_cli(
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--config-file",
            str(config_path),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertTrue(any("config.toml" in item for item in payload["assumptions"]))

    def test_auto_detects_superpowers_workflow_and_adds_review_roles(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "We already brainstormed the feature and need to continue with superpowers.",
                    "Use superpowers:writing-plans, then superpowers:subagent-driven-development, then verification-before-completion.",
                    "The work includes frontend, backend, and tests.",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertEqual(payload["workflow_profile"], "superpowers-plan")
        self.assertIn("planner.toml", payload["toml_files"])
        self.assertIn("spec-reviewer.toml", payload["toml_files"])
        self.assertTrue(any(item["id"] == "superpowers:writing-plans" for item in payload["workflow_integrations"]))
        self.assertTrue(any(step["id"] == "subagent-driven-development" for step in payload["workflow_steps"]))

    def test_auto_detects_openspec_core_workflow(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "Use OpenSpec for this feature.",
                    "Start with /opsx:propose, then /opsx:apply, and finish with /opsx:archive.",
                    "The app needs frontend and backend work.",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertEqual(payload["workflow_profile"], "openspec-core")
        self.assertTrue(any(step["id"] == "opsx:propose" for step in payload["workflow_steps"]))
        self.assertTrue(any(step["id"] == "opsx:archive" for step in payload["workflow_steps"]))
        self.assertIn("proposal-writer.toml", payload["toml_files"])
        self.assertIn("archiver.toml", payload["toml_files"])

    def test_auto_detects_openspec_expanded_workflow(self) -> None:
        input_path = self.make_input(
            "\n".join(
                [
                    "Use the expanded OpenSpec workflow.",
                    "Run /opsx:explore, /opsx:new, /opsx:continue, /opsx:ff, /opsx:apply, /opsx:verify, /opsx:sync, then /opsx:archive.",
                    "Need docs, schema, backend, frontend, and verification.",
                ]
            )
        )
        output_dir = self.make_output_dir()

        result = self.run_cli("--input", str(input_path), "--output-dir", str(output_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        self.assertEqual(payload["workflow_profile"], "openspec-expanded")
        self.assertTrue(any(step["id"] == "opsx:verify" for step in payload["workflow_steps"]))
        self.assertTrue(any(step["id"] == "opsx:sync" for step in payload["workflow_steps"]))
        self.assertIn("verifier.toml", payload["toml_files"])
        self.assertIn("sync-manager.toml", payload["toml_files"])

    def test_install_writes_agents_into_codex_home_and_records_manifest(self) -> None:
        input_path = self.make_input("Create docs, frontend, backend, and testing plans for a new web app.")
        output_dir = self.make_output_dir()
        codex_home = self.make_codex_home()

        result = self.run_cli(
            "--input",
            str(input_path),
            "--project-name",
            "install-demo",
            "--output-dir",
            str(output_dir),
            "--codex-home",
            str(codex_home),
            "--install",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json_from_stdout(result.stdout)
        agents_dir = codex_home / "agents"
        self.assertTrue((agents_dir / "default.toml").exists())
        self.assertTrue((agents_dir / "worker.toml").exists())
        self.assertTrue((agents_dir / "explorer.toml").exists())
        manifest = payload["install_manifest"]
        self.assertEqual(manifest["action"], "install")
        self.assertTrue(Path(manifest["path"]).exists())
        self.assertTrue(payload["installed_files"])

    def test_uninstall_restores_backups_and_removes_new_files(self) -> None:
        input_path = self.make_input("Create docs, frontend, backend, and testing plans for a new web app.")
        output_dir = self.make_output_dir()
        codex_home = self.make_codex_home()
        agents_dir = codex_home / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        original_default = 'name = "default"\ndescription = "preexisting"\n'
        (agents_dir / "default.toml").write_text(original_default, encoding="utf-8")

        install_result = self.run_cli(
            "--input",
            str(input_path),
            "--project-name",
            "restore-demo",
            "--output-dir",
            str(output_dir),
            "--codex-home",
            str(codex_home),
            "--install",
        )

        self.assertEqual(install_result.returncode, 0, msg=install_result.stderr or install_result.stdout)
        payload = self.load_json_from_stdout(install_result.stdout)
        self.assertNotEqual((agents_dir / "default.toml").read_text(encoding="utf-8"), original_default)

        uninstall_result = self.run_cli(
            "--uninstall",
            "--project-name",
            "restore-demo",
            "--codex-home",
            str(codex_home),
        )

        self.assertEqual(uninstall_result.returncode, 0, msg=uninstall_result.stderr or uninstall_result.stdout)
        self.assertEqual((agents_dir / "default.toml").read_text(encoding="utf-8"), original_default)
        self.assertFalse((agents_dir / "worker.toml").exists())
        self.assertFalse((agents_dir / "explorer.toml").exists())
        self.assertFalse(Path(payload["install_manifest"]["path"]).exists())


if __name__ == "__main__":
    unittest.main()
