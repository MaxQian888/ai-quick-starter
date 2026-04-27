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
    / "guarded-component-i18n-fix"
    / "scripts"
    / "build_component_i18n_audit.py"
)


class BuildComponentI18nAuditTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_root = WORKSPACE_ROOT / "guarded-component-i18n-fix" / ".tmp-tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        repo_root = temp_root / f"component-i18n-audit-{uuid.uuid4().hex}"
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

    def test_detects_next_intl_and_flags_duplicate_systems(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "next-intl": "^4.0.0",
                        }
                    }
                ),
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

        result = self.run_cli("--root", str(repo_root), "--target", "src/components")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["selected_system"]["name"], "next-intl")
        forbidden = "\n".join(payload["forbidden_actions"])
        self.assertIn("react-i18next", forbidden)

    def test_reports_hardcoded_component_strings_and_safe_fix_plan(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "react-i18next": "^15.0.0",
                        }
                    }
                ),
                "src/i18n.ts": "export const i18n = {};\n",
                "src/components/Greeting.tsx": (
                    "export function Greeting() {\n"
                    "  return <button title=\"Say hello\">Hello world</button>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--target", "src/components")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        finding = payload["component_findings"][0]
        self.assertEqual(finding["status"], "needs-localization")
        self.assertTrue(finding["candidate_strings"])
        self.assertEqual(payload["safe_fix_plan"][0]["operation"], "reuse-existing-i18n-hook")

    def test_marks_mixed_pattern_when_file_has_translation_hook_and_raw_text(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "react-i18next": "^15.0.0",
                        }
                    }
                ),
                "src/components/Banner.tsx": (
                    "import {useTranslation} from 'react-i18next';\n"
                    "export function Banner() {\n"
                    "  const {t} = useTranslation('banner');\n"
                    "  return <p>{t('title')} Save now</p>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--target", "src/components")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["component_findings"][0]["status"], "mixed-patterns")

    def test_marks_directory_blocked_when_system_detection_is_ambiguous(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "react-i18next": "^15.0.0",
                            "next-intl": "^4.0.0",
                        }
                    }
                ),
                "src/components/Example.tsx": (
                    "export function Example() {\n"
                    "  return <span>Plain text</span>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--target", "src/components")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["selected_system"]["confidence"], "low")
        self.assertTrue(any(item["status"] == "blocked" for item in payload["component_findings"]))

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "vue-i18n": "^9.0.0",
                        }
                    }
                ),
                "src/components/Card.vue": (
                    "<template><p>{{ $t('card.title') }}</p></template>\n"
                    "<script setup>\n"
                    "const title = 'noop'\n"
                    "</script>\n"
                ),
            }
        )

        result = self.run_cli("--root", str(repo_root), "--target", "src/components")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Detected I18n System", markdown)
        self.assertIn("## Component Findings", markdown)
        self.assertIn("## Forbidden Actions", markdown)


if __name__ == "__main__":
    unittest.main()




