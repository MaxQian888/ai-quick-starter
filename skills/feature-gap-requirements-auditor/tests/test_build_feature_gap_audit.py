from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = (
    WORKSPACE_ROOT
    / "feature-gap-requirements-auditor"
    / "scripts"
    / "build_feature_gap_audit.py"
)


class BuildFeatureGapAuditTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        repo_root = Path(tempfile.mkdtemp(prefix="feature-gap-auditor-"))
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

    def find_gap(self, payload: dict[str, object], text_fragment: str) -> dict[str, object]:
        for item in payload["feature_gap_candidates"]:
            if text_fragment.lower() in item["requirement_text"].lower():
                return item
        self.fail(f"Could not find gap containing '{text_fragment}'")

    def require_no_gap(self, payload: dict[str, object], text_fragment: str) -> None:
        for item in payload["feature_gap_candidates"]:
            if text_fragment.lower() in item["requirement_text"].lower():
                self.fail(f"Unexpected gap containing '{text_fragment}'")

    def find_guardrail(self, payload: dict[str, object], text_fragment: str) -> dict[str, object]:
        for item in payload["guardrail_findings"]:
            if text_fragment.lower() in item["requirement_text"].lower():
                return item
        self.fail(f"Could not find guardrail containing '{text_fragment}'")

    def test_marks_documented_feature_missing_when_source_has_no_matching_signal(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/profile-card-spec.md": (
                    "# Profile Card\n\n"
                    "## Requirements\n"
                    "- Support avatar upload with preview and removal.\n"
                    "- Show the current profile name.\n"
                ),
                "src/components/ProfileCard.tsx": (
                    "export function ProfileCard({ name }: { name: string }) {\n"
                    "  return <div>{name}</div>;\n"
                    "}\n"
                ),
                "src/components/ProfileCard.test.tsx": (
                    "import { ProfileCard } from './ProfileCard';\n"
                    "test('shows current profile name', () => {\n"
                    "  expect(ProfileCard).toBeDefined();\n"
                    "});\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/components/ProfileCard.tsx",
            "--doc",
            "docs/profile-card-spec.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        gap = self.find_gap(payload, "avatar upload")
        self.assertEqual(gap["status"], "missing")
        self.assertTrue(payload["detailed_requirements"])
        self.assertIn("avatar upload", payload["detailed_requirements"][0]["title"].lower())

    def test_marks_requirement_partial_when_only_some_signals_exist(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/metrics-panel.md": (
                    "# Metrics Panel\n\n"
                    "## Capabilities\n"
                    "- Provide loading and error states for metrics refresh.\n"
                ),
                "src/dashboard/MetricsPanel.tsx": (
                    "export function MetricsPanel({ isLoading, metrics }: Props) {\n"
                    "  if (isLoading) {\n"
                    "    return <div>Loading metrics...</div>;\n"
                    "  }\n"
                    "  return <ul>{metrics.map((metric) => <li key={metric.id}>{metric.name}</li>)}</ul>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/dashboard",
            "--doc",
            "docs/metrics-panel.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        gap = self.find_gap(payload, "loading and error states")
        self.assertEqual(gap["status"], "partial")

    def test_auto_discovers_target_readme_when_docs_are_not_explicitly_passed(self) -> None:
        repo_root = self.make_repo(
            {
                "src/profile/README.md": (
                    "# Profile Form\n\n"
                    "## Requirements\n"
                    "- Allow editing the display name.\n"
                ),
                "src/profile/ProfileForm.tsx": (
                    "export function ProfileForm() {\n"
                    "  return <form><input name=\"displayName\" /></form>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/profile",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        discovered = {entry["path"] for entry in payload["discovered_docs"]}
        self.assertIn("src/profile/README.md", discovered)
        self.assertTrue(payload["doc_requirements"])

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/toolbar.md": (
                    "# Toolbar\n\n"
                    "## Requirements\n"
                    "- Support export as CSV.\n"
                ),
                "src/toolbar/Toolbar.tsx": (
                    "export function Toolbar() {\n"
                    "  return <div>Toolbar</div>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/toolbar",
            "--doc",
            "docs/toolbar.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        markdown = markdown_path.read_text(encoding="utf-8")
        self.assertIn("## Request", markdown)
        self.assertIn("## Documentation Signals", markdown)
        self.assertIn("## Target Surface", markdown)
        self.assertIn("## Gap Candidates", markdown)
        self.assertIn("## Detailed Requirements", markdown)
        self.assertIn("## Blind Spots", markdown)

    def test_skips_container_lines_and_out_of_scope_entries_from_feature_gaps(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/editor-spec.md": (
                    "# Editor\n\n"
                    "## Requirements\n"
                    "- The editor should support:\n"
                    "  - Inline rename with save and cancel actions.\n"
                    "## Out of Scope\n"
                    "- Bulk delete across projects.\n"
                ),
                "src/editor/Editor.tsx": (
                    "export function Editor() {\n"
                    "  return <div>Editor</div>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/editor",
            "--doc",
            "docs/editor-spec.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.find_gap(payload, "Inline rename")
        self.require_no_gap(payload, "The editor should support")
        self.require_no_gap(payload, "Bulk delete across projects")

    def test_reports_guardrails_separately_without_promoting_them_to_missing_features(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/delete-flow.md": (
                    "# Delete Flow\n\n"
                    "## Requirements\n"
                    "- Allow deleting a saved item.\n"
                    "## Guardrails\n"
                    "- Do not delete immediately without confirmation.\n"
                ),
                "src/delete/DeleteButton.tsx": (
                    "export function DeleteButton() {\n"
                    "  return <button>Delete</button>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/delete",
            "--doc",
            "docs/delete-flow.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.find_gap(payload, "Allow deleting a saved item")
        self.require_no_gap(payload, "Do not delete immediately without confirmation")
        guardrail = self.find_guardrail(payload, "Do not delete immediately without confirmation")
        self.assertIn(guardrail["status"], {"missing", "partial", "covered"})

    def test_does_not_extract_feature_requirements_from_ancestor_context_docs_by_default(self) -> None:
        repo_root = self.make_repo(
            {
                "AGENTS.md": (
                    "# Repo Rules\n\n"
                    "## Requirements\n"
                    "- Support organization-wide deployment dashboards.\n"
                ),
                "src/profile/README.md": (
                    "# Profile\n\n"
                    "## Requirements\n"
                    "- Allow editing the display name.\n"
                ),
                "src/profile/ProfileForm.tsx": (
                    "export function ProfileForm() {\n"
                    "  return <form><input name=\"displayName\" /></form>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/profile",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        doc_texts = [item["text"] for item in payload["doc_requirements"]]
        self.assertIn("Allow editing the display name.", doc_texts)
        self.assertNotIn("Support organization-wide deployment dashboards.", doc_texts)

    def test_skips_contract_metadata_requirements_by_default(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/skill-spec.md": (
                    "# Skill Spec\n\n"
                    "## Planned Skill Metadata\n"
                    "- display_name: Profile Auditor\n"
                    "- description: Use when auditing profile gaps.\n"
                    "## Requirements\n"
                    "- Support avatar removal.\n"
                ),
                "src/profile/ProfileCard.tsx": (
                    "export function ProfileCard() {\n"
                    "  return <div>Profile</div>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/profile",
            "--doc",
            "docs/skill-spec.md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.find_gap(payload, "Support avatar removal")
        self.require_no_gap(payload, "display_name: Profile Auditor")
        self.require_no_gap(payload, "description: Use when auditing profile gaps")

    def test_can_include_contract_requirements_when_flag_is_set(self) -> None:
        repo_root = self.make_repo(
            {
                "docs/skill-spec.md": (
                    "# Skill Spec\n\n"
                    "## Planned Skill Metadata\n"
                    "- display_name: Profile Auditor\n"
                ),
                "src/profile/ProfileCard.tsx": (
                    "export function ProfileCard() {\n"
                    "  return <div>Profile</div>;\n"
                    "}\n"
                ),
            }
        )

        result = self.run_cli(
            "--root",
            str(repo_root),
            "--target",
            "src/profile",
            "--doc",
            "docs/skill-spec.md",
            "--include-contract-requirements",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_payload(result.stdout)
        self.find_gap(payload, "display_name: Profile Auditor")


if __name__ == "__main__":
    unittest.main()
