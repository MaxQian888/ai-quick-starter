from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "project-skill-builder" / "scripts" / "build_project_skill.py"
TMP_ROOT = WORKSPACE_ROOT / "project-skill-builder" / ".tmp-tests"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


class BuildProjectSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self._paths_to_cleanup: list[Path] = []

    def tearDown(self) -> None:
        for target in reversed(self._paths_to_cleanup):
            shutil.rmtree(target, ignore_errors=True)

    def make_temp_dir(self, prefix: str) -> Path:
        path = TMP_ROOT / f"{prefix}{uuid4().hex}"
        path.mkdir(parents=True, exist_ok=False)
        self._paths_to_cleanup.append(path)
        return path

    def make_repo(self, files: dict[str, str]) -> Path:
        root = self.make_temp_dir("source-")
        for relative_path, content in files.items():
            file_path = root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return root

    def run_cli(
        self,
        repo_root: Path,
        output_dir: Path,
        skill_name: str = "demo-repo-assistant",
        *extra_args: str,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--project-root",
            str(repo_root),
            "--skill-name",
            skill_name,
            "--output-dir",
            str(output_dir),
            *extra_args,
        ]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Missing {key}=... in stdout:\n{stdout}")

    def test_scaffolds_generated_skill_with_expected_files(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# Demo repo\n",
                "package.json": json.dumps(
                    {
                        "name": "demo-app",
                        "scripts": {
                            "dev": "vite",
                            "test": "vitest run",
                        },
                    }
                ),
                "src/main.ts": "console.log('ready')\n",
            }
        )
        output_dir = self.make_temp_dir("output-")

        result = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        skill_dir = self.read_output_path(result.stdout, "SKILL_DIR")
        analysis_json = self.read_output_path(result.stdout, "ANALYSIS_JSON")
        self.assertTrue((skill_dir / "SKILL.md").exists())
        self.assertTrue((skill_dir / "CLAUDE.md").exists())
        self.assertTrue((skill_dir / "agents" / "openai.yaml").exists())
        self.assertTrue((skill_dir / "references" / "project-map.md").exists())
        self.assertTrue((skill_dir / "references" / "working-rules.md").exists())
        self.assertTrue(analysis_json.exists())

        skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: demo-repo-assistant", skill_md)
        self.assertIn("demo-app", skill_md)

        claude_md = (skill_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("demo-repo-assistant", claude_md)

        project_map = (skill_dir / "references" / "project-map.md").read_text(encoding="utf-8")
        self.assertIn("package.json", project_map)
        self.assertIn("npm run dev", project_map)

    def test_collects_python_and_makefile_signals(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    'name = "service-core"\n'
                    "[tool.pytest.ini_options]\n"
                    'addopts = "-q"\n'
                    "[tool.ruff]\n"
                    "line-length = 100\n"
                ),
                "Makefile": "test:\n\tpytest -q\nlint:\n\truff check .\n",
                "src/server.py": "def main():\n    return None\n",
            }
        )
        output_dir = self.make_temp_dir("output-")

        result = self.run_cli(repo_root, output_dir, "service-core-guide")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        analysis_path = self.read_output_path(result.stdout, "ANALYSIS_JSON")
        payload = json.loads(analysis_path.read_text(encoding="utf-8"))
        commands = {entry["command"] for entry in payload["commands"]}
        self.assertIn("python -m pytest", commands)
        self.assertIn("python -m ruff check .", commands)
        self.assertIn("make test", commands)
        self.assertIn("make lint", commands)
        self.assertEqual(payload["project_name"], "service-core")

    def test_respects_include_and_exclude_filters(self) -> None:
        repo_root = self.make_repo(
            {
                "apps/web/package.json": json.dumps({"name": "web", "scripts": {"dev": "next dev"}}),
                "apps/web/app/page.tsx": "export default function Page() { return null }\n",
                "vendor/generated.js": "console.log('ignore')\n",
            }
        )
        output_dir = self.make_temp_dir("output-")

        result = self.run_cli(
            repo_root,
            output_dir,
            "web-skill",
            "--include",
            "apps/web",
            "--exclude",
            "vendor",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        analysis_path = self.read_output_path(result.stdout, "ANALYSIS_JSON")
        payload = json.loads(analysis_path.read_text(encoding="utf-8"))
        manifests = set(payload["summary"]["manifests"])
        self.assertIn("apps/web/package.json", manifests)
        self.assertEqual(payload["project_name"], "web")
        serialized = json.dumps(payload)
        self.assertNotIn("vendor/generated.js", serialized)

    def test_requires_force_to_replace_existing_generated_skill(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# Demo repo\n",
                "package.json": json.dumps({"name": "demo-app", "scripts": {"dev": "vite"}}),
            }
        )
        output_dir = self.make_temp_dir("output-")

        first = self.run_cli(repo_root, output_dir, "replaceable-skill")
        self.assertEqual(first.returncode, 0, msg=first.stderr or first.stdout)

        second = self.run_cli(repo_root, output_dir, "replaceable-skill")
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("--force", second.stderr or second.stdout)

        forced = self.run_cli(repo_root, output_dir, "replaceable-skill", "--force")
        self.assertEqual(forced.returncode, 0, msg=forced.stderr or forced.stdout)

    def test_skips_codex_uv_cache_noise_from_analysis(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# Demo repo\n",
                "package.json": json.dumps({"name": "demo-app", "scripts": {"dev": "vite"}}),
                ".codex-uv-cache/noise/generated.py": "print('noise')\n",
                ".uv-cache-codex/noise/generated.py": "print('noise')\n",
                "src/main.ts": "console.log('ready')\n",
            }
        )
        output_dir = self.make_temp_dir("output-")

        result = self.run_cli(repo_root, output_dir, "cache-safe-skill")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        analysis_path = self.read_output_path(result.stdout, "ANALYSIS_JSON")
        payload = json.loads(analysis_path.read_text(encoding="utf-8"))
        serialized = json.dumps(payload)
        self.assertNotIn(".codex-uv-cache", serialized)
        self.assertNotIn(".uv-cache-codex", serialized)

    def test_records_scan_limit_when_max_files_is_hit(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# Demo repo\n",
                "package.json": json.dumps({"name": "demo-app", "scripts": {"dev": "vite"}}),
                "src/a.ts": "export const a = 1;\n",
                "src/b.ts": "export const b = 2;\n",
                "src/c.ts": "export const c = 3;\n",
            }
        )
        output_dir = self.make_temp_dir("output-")

        result = self.run_cli(repo_root, output_dir, "limited-skill", "--max-files", "2")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        analysis_path = self.read_output_path(result.stdout, "ANALYSIS_JSON")
        payload = json.loads(analysis_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["limits"])
        self.assertIn("Stopped after indexing 2 matching files", payload["limits"][0]["detail"])

    def test_generated_metadata_matches_skill_and_project_identity(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo-app", "scripts": {"dev": "vite", "test": "vitest run"}}),
                "src/main.ts": "console.log('ready')\n",
            }
        )
        output_dir = self.make_temp_dir("output-")

        result = self.run_cli(repo_root, output_dir, "demo-app-helper")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        skill_dir = self.read_output_path(result.stdout, "SKILL_DIR")
        openai_yaml = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
        working_rules = (skill_dir / "references" / "working-rules.md").read_text(encoding="utf-8")

        self.assertIn('display_name: "Demo App Helper"', openai_yaml)
        self.assertIn("Use $demo-app-helper", openai_yaml)
        self.assertIn("`demo-app`", working_rules)
        self.assertIn("`$demo-app-helper`", working_rules)


if __name__ == "__main__":
    unittest.main()
