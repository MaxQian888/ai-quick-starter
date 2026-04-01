from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "audit_comment_surface.py"


def load_module():
    if not SCRIPT.exists():
        raise AssertionError(f"Missing script: {SCRIPT}")
    module_spec = importlib.util.spec_from_file_location("audit_comment_surface", SCRIPT)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


class AuditCommentSurfaceTests(unittest.TestCase):
    def make_tree(self, files: dict[str, str]) -> Path:
        root = Path(tempfile.mkdtemp(prefix="guarded-code-comment-editor-"))
        for relative_path, content in files.items():
            file_path = root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return root

    def test_detects_typescript_style_and_suspicious_comments(self) -> None:
        module = load_module()
        root = self.make_tree(
            {
                "src/widget.ts": """
                    // This function handles the save operation.
                    export function saveWidget(value: string) {
                      // Initialize the variable.
                      const trimmed = value.trim();
                      return trimmed;
                    }
                """,
                "src/natural.ts": """
                    export function buildSlug(value: string) {
                      // Keep spaces out of route params so generated links stay stable.
                      return value.trim().replace(/\\s+/g, "-");
                    }
                """,
            }
        )

        payload = module.analyze_target(root, root / "src")

        self.assertEqual(payload["selected_style"]["primary_language"], "typescript")
        self.assertEqual(payload["summary"]["languages"]["typescript"], 2)
        self.assertGreaterEqual(payload["summary"]["suspicious_comment_count"], 2)
        self.assertEqual(payload["style_exemplars"][0]["path"], "src/natural.ts")

        widget_file = next(item for item in payload["file_findings"] if item["path"] == "src/widget.ts")
        self.assertEqual(widget_file["language"], "typescript")
        self.assertEqual(len(widget_file["suspicious_comments"]), 2)
        self.assertIn("rewrite-generic-comment", widget_file["needs_review"])

    def test_detects_python_docstrings_and_prefers_docstring_style(self) -> None:
        module = load_module()
        root = self.make_tree(
            {
                "pkg/worker.py": '''
                    """Background worker helpers."""

                    def run(job_id: str) -> str:
                        """Return a normalized job identifier for downstream logging."""
                        # Keep the prefix stable because another service parses it.
                        return f"job:{job_id.strip()}"
                ''',
                "pkg/helpers.py": '''
                    def clean_name(raw: str) -> str:
                        """Collapse extra spaces before persisting the display name."""
                        return " ".join(raw.split())
                ''',
            }
        )

        payload = module.analyze_target(root, root / "pkg")

        self.assertEqual(payload["selected_style"]["primary_language"], "python")
        self.assertEqual(payload["selected_style"]["docstring_style"], "docstring-heavy")
        self.assertEqual(payload["summary"]["languages"]["python"], 2)
        self.assertGreaterEqual(payload["summary"]["docstring_blocks"], 3)

    def test_detects_shell_and_powershell_comment_styles(self) -> None:
        module = load_module()
        root = self.make_tree(
            {
                "scripts/build.sh": """
                    # Keep the workspace root explicit so callers can invoke the script anywhere.
                    ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
                    echo "$ROOT_DIR"
                """,
                "scripts/sync.ps1": """
                    # Reuse the literal path variant because user-supplied paths may contain wildcards.
                    param([string]$TargetPath)
                    Get-Item -LiteralPath $TargetPath
                """,
            }
        )

        payload = module.analyze_target(root, root / "scripts")

        self.assertEqual(payload["summary"]["languages"]["shell"], 1)
        self.assertEqual(payload["summary"]["languages"]["powershell"], 1)
        self.assertIn("shell", {item["language"] for item in payload["file_findings"]})
        self.assertIn("powershell", {item["language"] for item in payload["file_findings"]})

    def test_cli_json_output(self) -> None:
        root = self.make_tree(
            {
                "src/sample.tsx": """
                    export function Panel() {
                      // Keep the title inline because the layout collapses on mobile.
                      return <h1>Dashboard</h1>;
                    }
                """,
            }
        )

        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(root),
                "--target",
                str(root / "src"),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_style"]["primary_language"], "tsx")
        self.assertEqual(payload["summary"]["file_count"], 1)
        self.assertEqual(payload["summary"]["languages"]["tsx"], 1)


if __name__ == "__main__":
    unittest.main()
