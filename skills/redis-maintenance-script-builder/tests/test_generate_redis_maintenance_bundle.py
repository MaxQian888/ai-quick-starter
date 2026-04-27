from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "generate_redis_maintenance_bundle.py"
TMP_ROOT = SKILL_ROOT / ".tmp-tests"


class GenerateRedisMaintenanceBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def make_output_dir(self) -> Path:
        output_dir = TMP_ROOT / f"bundle-{uuid.uuid4().hex}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def run_cli(self, task: str, shell: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object], Path, Path, Path]:
        output_dir = self.make_output_dir()
        json_path = output_dir / "redis-maintenance-bundle.json"
        markdown_path = output_dir / "redis-maintenance-bundle.md"
        command = [
            sys.executable,
            str(SCRIPT),
            "--task",
            task,
            "--shell",
            shell,
            "--output-dir",
            str(output_dir),
            "--json-out",
            str(json_path),
            "--markdown-out",
            str(markdown_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        payload = (
            json.loads(json_path.read_text(encoding="utf-8"))
            if json_path.exists()
            else {}
        )
        script_path = output_dir / payload.get("script_name", "")
        return result, payload, markdown_path, json_path, script_path

    def test_generates_powershell_health_check_bundle(self) -> None:
        result, payload, markdown_path, json_path, script_path = self.run_cli(
            "health-check",
            "powershell",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(json_path.exists())
        self.assertTrue(markdown_path.exists())
        self.assertEqual(payload["task"], "health-check")
        self.assertEqual(payload["shell"], "powershell")
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["script_name"], "redis-health-check.ps1")
        script_text = script_path.read_text(encoding="utf-8")
        self.assertIn("PING", script_text)
        self.assertIn("INFO memory", script_text)
        self.assertIn("INFO stats", script_text)
        self.assertIn("REDIS_URL", script_text)
        self.assertIn("## Generated Script", markdown_path.read_text(encoding="utf-8"))

    def test_generates_python_memory_audit_bundle(self) -> None:
        result, payload, _, _, script_path = self.run_cli(
            "memory-audit",
            "python",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(payload["task"], "memory-audit")
        self.assertEqual(payload["shell"], "python")
        self.assertEqual(payload["risk_level"], "medium")
        self.assertEqual(payload["script_name"], "redis-memory-audit.py")
        self.assertIn("redis.from_url", script_path.read_text(encoding="utf-8"))
        self.assertIn("info(section=\"memory\")", script_path.read_text(encoding="utf-8"))
        self.assertIn("memory_stats", script_path.read_text(encoding="utf-8"))
        self.assertIn("scan_iter", script_path.read_text(encoding="utf-8"))
        self.assertIn("REDIS_URL", payload["env_vars"])

    def test_generates_bash_slowlog_report_bundle(self) -> None:
        result, payload, _, _, script_path = self.run_cli(
            "slowlog-report",
            "bash",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(payload["task"], "slowlog-report")
        self.assertEqual(payload["shell"], "bash")
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["script_name"], "redis-slowlog-report.sh")
        script_text = script_path.read_text(encoding="utf-8")
        self.assertIn("SLOWLOG LEN", script_text)
        self.assertIn("SLOWLOG GET", script_text)
        self.assertIn("LATENCY LATEST", script_text)

    def test_generates_client_report_bundle(self) -> None:
        result, payload, _, _, script_path = self.run_cli(
            "client-report",
            "python",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(payload["task"], "client-report")
        self.assertEqual(payload["shell"], "python")
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["script_name"], "redis-client-report.py")
        script_text = script_path.read_text(encoding="utf-8")
        self.assertIn("CLIENT LIST", script_text)
        self.assertIn("CLIENT INFO", script_text)
        self.assertIn("info(section=\"clients\")", script_text)
        self.assertIn("info(section=\"replication\")", script_text)

    def test_cleanup_bundle_defaults_to_dry_run_and_uses_unlink(self) -> None:
        result, payload, _, _, script_path = self.run_cli(
            "cleanup-by-pattern",
            "powershell",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(payload["task"], "cleanup-by-pattern")
        self.assertEqual(payload["shell"], "powershell")
        self.assertEqual(payload["risk_level"], "high")
        self.assertEqual(payload["script_name"], "redis-cleanup-by-pattern.ps1")
        script_text = script_path.read_text(encoding="utf-8")
        self.assertIn("[switch]$Execute", script_text)
        self.assertIn("UNLINK", script_text)
        self.assertIn("--scan", script_text)
        self.assertIn("dry run", script_text.lower())
        self.assertTrue(
            any("dry-run" in note.lower() for note in payload["safety_notes"])
        )


if __name__ == "__main__":
    unittest.main()
