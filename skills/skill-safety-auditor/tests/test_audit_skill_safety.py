from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
import unittest
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_skill_safety.py"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


class AuditSkillSafetyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = WORKSPACE_ROOT / "skill-safety-auditor" / ".tmp-tests"
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if self.temp_root.exists():
            for child in self.temp_root.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
            try:
                self.temp_root.rmdir()
            except OSError:
                pass

    def make_skill(
        self,
        *,
        description: str = "Use when auditing one narrow skill workflow before publishing.",
        body: str = "Run the local helper script and review the report.",
        extra_files: dict[str, str] | None = None,
        include_openai: bool = True,
    ) -> Path:
        skill_dir = self.temp_root / f"fixture-{uuid.uuid4().hex}"
        skill_dir.mkdir(parents=True, exist_ok=False)
        write_file(
            skill_dir / "SKILL.md",
            f"""
            ---
            name: fixture-skill
            description: {description}
            ---

            # Fixture Skill

            {body}
            """,
        )
        if include_openai:
            write_file(
                skill_dir / "agents" / "openai.yaml",
                """
                interface:
                  display_name: "Fixture Skill"
                  short_description: "Audit a fixture skill safely"
                  default_prompt: "Use $fixture-skill to inspect a fixture skill."
                """,
            )
        for relative_path, content in (extra_files or {}).items():
            write_file(skill_dir / relative_path, content)
        return skill_dir

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def load_payload(self, stdout: str) -> dict[str, object]:
        json_path = self.read_output_path(stdout, "JSON_OUT")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def test_detects_hardcoded_secret_but_ignores_placeholder(self) -> None:
        skill_dir = self.make_skill(
            body="""
            Export the key:

            ```bash
            export OPENAI_API_KEY="sk-live-1234567890abcdefghijklmnop"
            export ANTHROPIC_API_KEY="<YOUR_API_KEY>"
            ```
            """,
            extra_files={"tests/test_placeholder.py": "def test_ok():\n    assert True\n"},
        )

        result = self.run_cli("--skill-path", str(skill_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        categories = {finding["category"] for finding in payload["findings"]}
        self.assertIn("hardcoded-secret", categories)
        evidence_text = "\n".join(str(finding["evidence"]) for finding in payload["findings"])
        self.assertNotIn("<YOUR_API_KEY>", evidence_text)

    def test_detects_dangerous_commands_and_blocks_execution(self) -> None:
        skill_dir = self.make_skill(
            body="""
            Run the cleanup command directly:

            ```powershell
            Remove-Item -Recurse -Force C:\\Users\\Public\\Downloads
            ```
            """,
            extra_files={"tests/test_placeholder.py": "def test_ok():\n    assert True\n"},
        )

        result = self.run_cli("--skill-path", str(skill_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        categories = {finding["category"] for finding in payload["findings"]}
        self.assertIn("dangerous-command", categories)
        blocked_actions = "\n".join(payload["blocked_actions"])
        self.assertIn("Do not execute", blocked_actions)

    def test_detects_outside_workspace_write_instruction(self) -> None:
        skill_dir = self.make_skill(
            body="""
            Save the generated artifact to `C:/Users/qwdma/.ssh/id_rsa.backup` before continuing.
            """,
            extra_files={"tests/test_placeholder.py": "def test_ok():\n    assert True\n"},
        )

        result = self.run_cli("--skill-path", str(skill_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        categories = {finding["category"] for finding in payload["findings"]}
        self.assertIn("outside-workspace-write", categories)

    def test_detects_missing_runtime_verification_for_script_backed_skill(self) -> None:
        skill_dir = self.make_skill(
            extra_files={"scripts/helper.py": "print('ok')\n"},
        )

        result = self.run_cli("--skill-path", str(skill_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        categories = {finding["category"] for finding in payload["findings"]}
        self.assertIn("missing-runtime-verification", categories)
        safe_ops = {step["operation"] for step in payload["safe_fix_plan"]}
        self.assertIn("add-runtime-verification", safe_ops)

    def test_detects_over_broad_trigger_description(self) -> None:
        skill_dir = self.make_skill(
            description="Use when working on any code or any repository task.",
            extra_files={"tests/test_placeholder.py": "def test_ok():\n    assert True\n"},
        )

        result = self.run_cli("--skill-path", str(skill_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        categories = {finding["category"] for finding in payload["findings"]}
        self.assertIn("trigger-too-broad", categories)

    def test_writes_required_json_and_markdown_sections(self) -> None:
        skill_dir = self.make_skill(
            extra_files={"tests/test_placeholder.py": "def test_ok():\n    assert True\n"},
        )

        result = self.run_cli("--skill-path", str(skill_dir))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertIn("overall_status", payload)
        self.assertIn("risk_score", payload)
        self.assertIn("safe_fix_plan", payload)
        self.assertIn("blind_spots", payload)

        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Overall Status", markdown)
        self.assertIn("## Findings", markdown)
        self.assertIn("## Safe Fix Plan", markdown)
        self.assertIn("## Blocked Actions", markdown)


if __name__ == "__main__":
    unittest.main()
