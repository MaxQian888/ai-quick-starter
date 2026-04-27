from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "tauri-rust-component-splitter" / "scripts" / "plan_tauri_rust_split.py"


class PlanTauriRustSplitTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="tauri-rust-split-"))
        for relative_path, content in files.items():
            file_path = temp_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def run_cli(self, repo_root: Path, target: str, *extra_args: str) -> tuple[dict[str, object], str]:
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--root",
                str(repo_root),
                "--target",
                target,
                *extra_args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        json_path = self.read_output_path(result.stdout, "JSON_OUT")
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        return json.loads(json_path.read_text(encoding="utf-8")), markdown_path.read_text(encoding="utf-8")

    def run_cli_expect_failure(self, repo_root: Path, target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--root",
                str(repo_root),
                "--target",
                target,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_detects_tauri_commands_and_service_candidates(self) -> None:
        repo_root = self.make_repo(
            {
                "src-tauri/src/app.rs": """
use std::sync::Mutex;

pub struct AppState {
    pub online: Mutex<bool>,
}

pub struct NotificationService;

impl NotificationService {
    pub fn send_system_notification(&self, title: &str) -> Result<(), String> {
        let _ = title;
        Ok(())
    }
}

#[tauri::command]
pub async fn ping_app(state: tauri::State<'_, AppState>) -> Result<String, String> {
    let _ = state;
    Ok("pong".into())
}
""".strip()
            }
        )

        payload, _markdown = self.run_cli(repo_root, "src-tauri/src/app.rs")

        proposed_paths = {entry["path"] for entry in payload["proposed_files"]}
        self.assertIn("src-tauri/src/commands/app_commands.rs", proposed_paths)
        self.assertIn("src-tauri/src/services/notification_service.rs", proposed_paths)
        self.assertIn("src-tauri/src/state/app_state.rs", proposed_paths)

    def test_reports_generic_module_and_symbol_names(self) -> None:
        repo_root = self.make_repo(
            {
                "src-tauri/src/common.rs": """
pub struct helperThing;

pub fn DoThing() {}
""".strip()
            }
        )

        payload, _markdown = self.run_cli(repo_root, "src-tauri/src/common.rs")

        rules = {entry["rule"] for entry in payload["naming_findings"]}
        self.assertIn("generic-module-name", rules)
        self.assertIn("type-should-be-pascal-case", rules)
        self.assertIn("function-should-be-snake-case", rules)

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "src-tauri/src/app.rs": """
#[tauri::command]
pub fn open_window() {}
""".strip()
            }
        )

        _payload, markdown = self.run_cli(repo_root, "src-tauri/src/app.rs")

        self.assertIn("## Project Context", markdown)
        self.assertIn("## Naming Findings", markdown)
        self.assertIn("## Proposed File Layout", markdown)
        self.assertIn("## Migration Phases", markdown)

    def test_scaffold_creates_placeholder_files(self) -> None:
        repo_root = self.make_repo(
            {
                "src-tauri/src/app.rs": """
pub struct AppState {
    pub ready: bool,
}

#[tauri::command]
pub fn open_window() {}
""".strip()
            }
        )

        payload, _markdown = self.run_cli(repo_root, "src-tauri/src/app.rs", "--scaffold")

        self.assertTrue((repo_root / "src-tauri/src/commands/app_commands.rs").exists())
        self.assertTrue((repo_root / "src-tauri/src/commands/mod.rs").exists())
        self.assertTrue((repo_root / "src-tauri/src/state/app_state.rs").exists())
        self.assertTrue(payload["scaffold_created"])

    def test_rejects_targets_outside_src_tauri(self) -> None:
        repo_root = self.make_repo(
            {
                "src/lib.rs": "pub fn helper() {}\n",
            }
        )

        result = self.run_cli_expect_failure(repo_root, "src/lib.rs")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("src-tauri", result.stderr)


if __name__ == "__main__":
    unittest.main()
