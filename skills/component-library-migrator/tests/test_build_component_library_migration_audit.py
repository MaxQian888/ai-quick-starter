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
    / "component-library-migrator"
    / "scripts"
    / "build_component_library_migration_audit.py"
)


class BuildComponentLibraryMigrationAuditTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_root = WORKSPACE_ROOT / "component-library-migrator" / ".tmp-tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        repo_root = temp_root / f"component-library-migrator-{uuid.uuid4().hex}"
        repo_root.mkdir(parents=True, exist_ok=False)
        for relative_path, content in files.items():
            file_path = repo_root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return repo_root

    def run_cli(self, repo_root: Path, target: str, library: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--root",
            str(repo_root),
            "--target",
            target,
            "--library",
            library,
            *extra_args,
        ]
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

    def test_normalizes_builtin_library_aliases(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/ButtonRow.tsx": (
                    "export function ButtonRow() {\n"
                    "  return <button>Save</button>;\n"
                    "}\n"
                )
            }
        )

        result = self.run_cli(repo_root, "src/components", "MUI")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["target_library"]["canonical_name"], "mui")
        self.assertTrue(payload["target_library"]["is_builtin"])

    def test_reports_simple_button_candidate_for_builtin_target(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/ButtonRow.tsx": (
                    "export function ButtonRow() {\n"
                    "  return <button className=\"primary\">Save</button>;\n"
                    "}\n"
                )
            }
        )

        result = self.run_cli(repo_root, "src/components", "shadcn/ui")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        finding = payload["component_findings"][0]
        self.assertEqual(finding["status"], "safe-candidate")
        self.assertEqual(payload["candidate_mappings"][0]["target_component"], "Button")
        self.assertTrue(payload["safe_fix_plan"])

    def test_blocks_custom_wrapper_components(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/PrimaryButton.tsx": (
                    "export function PrimaryButton(props) {\n"
                    "  return <button data-variant=\"primary\" {...props} />;\n"
                    "}\n"
                ),
                "src/screens/Profile.tsx": (
                    "import { PrimaryButton } from '../components/PrimaryButton';\n"
                    "export function Profile() {\n"
                    "  return <PrimaryButton>Save</PrimaryButton>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(repo_root, "src/screens", "chakra-ui")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["component_findings"][0]["status"], "blocked")
        self.assertFalse(payload["safe_fix_plan"])

    def test_unsupported_library_downgrades_to_audit_only(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/Form.tsx": (
                    "export function Form() {\n"
                    "  return <input placeholder=\"Email\" />;\n"
                    "}\n"
                )
            }
        )

        result = self.run_cli(repo_root, "src/components", "primevue")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertFalse(payload["target_library"]["is_builtin"])
        self.assertEqual(payload["mode"], "audit-only")
        self.assertFalse(payload["safe_fix_plan"])

    def test_complex_dialog_pattern_is_not_auto_migrated(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/ProfileDialog.tsx": (
                    "export function ProfileDialog({ open, onClose, title, children }) {\n"
                    "  if (!open) return null;\n"
                    "  return (\n"
                    "    <div role=\"dialog\" aria-modal=\"true\">\n"
                    "      <header>\n"
                    "        <h2>{title}</h2>\n"
                    "        <button onClick={onClose}>Close</button>\n"
                    "      </header>\n"
                    "      <section>{children}</section>\n"
                    "    </div>\n"
                    "  );\n"
                    "}\n"
                )
            }
        )

        result = self.run_cli(repo_root, "src/components", "ant-design")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.assertEqual(payload["component_findings"][0]["status"], "blocked")
        self.assertTrue(payload["blocked_reasons"])

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/InputRow.tsx": (
                    "export function InputRow() {\n"
                    "  return <input placeholder=\"Email\" aria-label=\"Email\" />;\n"
                    "}\n"
                )
            }
        )

        result = self.run_cli(repo_root, "src/components", "heroui")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Request", markdown)
        self.assertIn("## Target Library", markdown)
        self.assertIn("## Component Findings", markdown)
        self.assertIn("## Candidate Mappings", markdown)
        self.assertIn("## Safe Fix Plan", markdown)
        self.assertIn("## Forbidden Actions", markdown)


if __name__ == "__main__":
    unittest.main()
