from __future__ import annotations

import json
import subprocess
import uuid
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = (
    WORKSPACE_ROOT
    / "guarded-project-i18n-support"
    / "scripts"
    / "build_project_i18n_plan.py"
)


class BuildProjectI18nPlanTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_root = WORKSPACE_ROOT / "guarded-project-i18n-support" / ".tmp-tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        repo_root = temp_root / f"project-i18n-plan-{uuid.uuid4().hex}"
        repo_root.mkdir(parents=True, exist_ok=False)
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return repo_root

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [str(PYTHON), str(SCRIPT), *args]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def load_payload(self, stdout: str) -> dict[str, object]:
        json_path = self.read_output_path(stdout, "JSON_OUT")
        return json.loads(json_path.read_text(encoding="utf-8"))

    def test_reuses_existing_next_intl_stack(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "next": "^16.0.0",
                            "react": "^19.0.0",
                            "next-intl": "^4.0.0",
                        }
                    }
                ),
                "app/page.tsx": "export default function Page() { return <main />; }\n",
                "src/i18n/request.ts": "export async function getRequestConfig() {}\n",
                "src/components/Hero.tsx": (
                    "import {useTranslations} from 'next-intl';\n"
                    "export function Hero() {\n"
                    "  const t = useTranslations('Hero');\n"
                    "  return <h1>{t('title')}</h1>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["recommended_strategy"]["mode"], "extend-existing")
        self.assertEqual(payload["recommended_strategy"]["system"], "next-intl")

    def test_recommends_next_intl_for_greenfield_next_project(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "next": "^16.0.0",
                            "react": "^19.0.0",
                        }
                    }
                ),
                "app/page.tsx": "export default function Page() { return <main>Hello</main>; }\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["recommended_strategy"]["mode"], "introduce-new")
        self.assertEqual(payload["recommended_strategy"]["system"], "next-intl")

    def test_recommends_react_i18next_for_react_spa(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "react": "^19.0.0",
                            "vite": "^7.0.0",
                            "react-router-dom": "^7.0.0",
                        }
                    }
                ),
                "src/main.tsx": "import React from 'react';\n",
                "src/App.tsx": "export function App() { return <main>Hello</main>; }\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["recommended_strategy"]["system"], "react-i18next")
        self.assertEqual(payload["recommended_strategy"]["mode"], "introduce-new")

    def test_blocks_ambiguous_existing_systems(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "next": "^16.0.0",
                            "react": "^19.0.0",
                            "next-intl": "^4.0.0",
                            "react-i18next": "^15.0.0",
                            "i18next": "^25.0.0",
                        }
                    }
                ),
                "app/page.tsx": "export default function Page() { return <main />; }\n",
                "src/i18n/request.ts": "export async function getRequestConfig() {}\n",
                "src/i18n.ts": "export const i18n = {};\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["recommended_strategy"]["mode"], "blocked")
        self.assertEqual(payload["selected_system"]["confidence"], "low")

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": "[project]\nname = 'demo'\nversion = '0.1.0'\n",
                "app.py": "print('hello')\n",
            }
        )

        result = self.run_cli("--root", str(repo_root))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Project Profile", markdown)
        self.assertIn("## Recommended Strategy", markdown)
        self.assertIn("## Verification Plan", markdown)


if __name__ == "__main__":
    unittest.main()
