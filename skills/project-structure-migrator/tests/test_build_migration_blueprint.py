from __future__ import annotations

import json
import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SKILL_ROOT = WORKSPACE_ROOT / "project-structure-migrator"
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = SKILL_ROOT / "scripts" / "build_migration_blueprint.py"
TMP_ROOT = SKILL_ROOT / ".tmp-tests"


class BuildMigrationBlueprintTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def make_repo(self, files: dict[str, str]) -> Path:
        repo_root = TMP_ROOT / f"migration-blueprint-{uuid.uuid4().hex}"
        repo_root.mkdir(parents=True, exist_ok=True)
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return repo_root

    def make_output_dir(self) -> Path:
        output_dir = TMP_ROOT / f"migration-output-{uuid.uuid4().hex}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def run_cli(self, repo_root: Path, output_dir: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
        json_path = output_dir / "blueprint.json"
        markdown_path = output_dir / "blueprint.md"
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--project-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--json-out",
            str(json_path),
            "--markdown-out",
            str(markdown_path),
            *args,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result, json_path, markdown_path

    def load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def test_detects_workspace_repo_as_monorepo_migration_surface(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo-root",
                        "private": True,
                        "workspaces": ["apps/*", "packages/*"],
                    }
                ),
                "pnpm-workspace.yaml": "packages:\n  - apps/*\n  - packages/*\n",
                "apps/web/package.json": json.dumps({"name": "@demo/web"}),
                "packages/ui/package.json": json.dumps({"name": "@demo/ui"}),
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, markdown_path = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["project_profile"]["stack"], "js-ts")
        self.assertEqual(payload["migration_classification"]["type"], "monorepo")
        self.assertTrue(payload["migration_classification"]["confidence"] >= 0.8)
        self.assertTrue(markdown_path.exists())

    def test_detects_mixed_concern_single_app_as_restructure_surface(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "legacy-app",
                        "scripts": {
                            "build": "vite build",
                            "test": "vitest run",
                        },
                    }
                ),
                "src/components/button.tsx": "export const Button = () => null;\n",
                "src/services/api.ts": "export async function load() { return []; }\n",
                "src/utils/format.ts": "export const format = () => '';\n",
                "src/pages/home.tsx": "export default function Home() { return null; }\n",
                ".github/workflows/ci.yml": "steps:\n  - run: pnpm test\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _ = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["migration_classification"]["type"], "restructure")
        self.assertTrue(payload["current_structure"]["mixed_concerns"])
        self.assertTrue(payload["target_structure"]["recommended_patterns"])
        self.assertTrue(payload["migration_batches"])

    def test_outputs_required_contract_fields_and_guardrails(self) -> None:
        repo_root = self.make_repo(
            {
                "README.md": "# fixture\n",
                "src/app.py": "print('hello')\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, markdown_path = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(
            sorted(payload.keys()),
            sorted(
                [
                    "current_structure",
                    "forbidden_moves",
                    "migration_batches",
                    "migration_classification",
                    "open_questions",
                    "project_profile",
                    "risk_register",
                    "target_structure",
                    "verification_plan",
                ]
            ),
        )
        self.assertTrue(payload["forbidden_moves"])
        self.assertIn("final", payload["verification_plan"])
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Project Profile", markdown)
        self.assertIn("## Forbidden Moves", markdown)
        self.assertIn("## Open Questions", markdown)

    def test_treats_root_package_workspaces_as_monorepo_signal_without_extra_workspace_files(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "workspace-root",
                        "private": True,
                        "workspaces": ["apps/*", "packages/*"],
                    }
                ),
                "apps/web/src/index.ts": "export const app = true;\n",
                "packages/ui/src/button.ts": "export const Button = {};\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _ = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["migration_classification"]["type"], "monorepo")
        self.assertTrue(payload["migration_classification"]["confidence"] >= 0.8)

    def test_detects_top_level_mixed_concerns_when_repo_has_no_src_directory(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "legacy-top-level-app",
                        "scripts": {
                            "build": "vite build",
                        },
                    }
                ),
                "components/button.tsx": "export const Button = () => null;\n",
                "services/api.ts": "export async function load() { return []; }\n",
                "utils/format.ts": "export const format = () => '';\n",
                "pages/home.tsx": "export default function Home() { return null; }\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _ = self.run_cli(repo_root, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        self.assertEqual(payload["migration_classification"]["type"], "restructure")
        self.assertTrue(payload["current_structure"]["mixed_concerns"])
        self.assertIn("components", payload["current_structure"]["coupling_hotspots"])
        self.assertTrue(payload["migration_classification"]["confidence"] >= 0.75)

    def test_respects_explicit_nested_output_paths(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"name": "demo"}),
                "src/components/button.tsx": "export const Button = () => null;\n",
                "src/services/api.ts": "export async function load() { return []; }\n",
                "src/utils/format.ts": "export const format = () => '';\n",
            }
        )
        output_dir = self.make_output_dir()
        json_out = output_dir / "reports" / "nested" / "plan.json"
        markdown_out = output_dir / "reports" / "nested" / "plan.md"

        result, _, _ = self.run_cli(
            repo_root,
            output_dir,
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(json_out.exists(), str(json_out))
        self.assertTrue(markdown_out.exists(), str(markdown_out))
        payload = self.load_json(json_out)
        self.assertEqual(payload["project_profile"]["project_root"], str(repo_root.resolve()))


if __name__ == "__main__":
    unittest.main()
