from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
import unittest
import uuid
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SKILL_ROOT = WORKSPACE_ROOT / "powershell-terminal-config-sync"
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = SKILL_ROOT / "scripts" / "build_shell_config_sync_plan.py"
TMP_ROOT = SKILL_ROOT / ".tmp-tests"


class BuildShellConfigSyncPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if TMP_ROOT.exists():
            shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def make_source_tree(self, files: dict[str, str]) -> tuple[Path, Path]:
        root = TMP_ROOT / f"source-{uuid.uuid4().hex}"
        source_home = root / "home"
        source_localappdata = root / "localappdata"
        source_home.mkdir(parents=True, exist_ok=True)
        source_localappdata.mkdir(parents=True, exist_ok=True)
        for relative_path, content in files.items():
            target_path = root / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
        return source_home, source_localappdata

    def make_output_dir(self) -> Path:
        output_dir = TMP_ROOT / f"output-{uuid.uuid4().hex}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def run_cli(self, source_home: Path, source_localappdata: Path, output_dir: Path) -> tuple[subprocess.CompletedProcess[str], Path, Path, Path]:
        json_path = output_dir / "shell-config-sync-bundle.json"
        markdown_path = output_dir / "shell-config-sync-bundle.md"
        sync_script = output_dir / "sync-shell-config.ps1"
        command = [
            str(PYTHON),
            str(SCRIPT),
            "--source-home",
            str(source_home),
            "--source-localappdata",
            str(source_localappdata),
            "--output-dir",
            str(output_dir),
            "--json-out",
            str(json_path),
            "--markdown-out",
            str(markdown_path),
            "--script-out",
            str(sync_script),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result, json_path, markdown_path, sync_script

    def load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builds_bundle_for_profiles_terminal_and_dependencies(self) -> None:
        source_home, source_localappdata = self.make_source_tree(
            {
                "home/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1": textwrap.dedent(
                    """
                    oh-my-posh init pwsh --config "$HOME\\night-owl.omp.json" | Invoke-Expression
                    . "$HOME\\Documents\\WindowsPowerShell\\aliases.ps1"
                    Import-Module posh-git
                    """
                ).strip()
                + "\n",
                "home/night-owl.omp.json": "{\n  \"name\": \"night-owl\"\n}\n",
                "home/Documents/WindowsPowerShell/aliases.ps1": "Set-Alias ll Get-ChildItem\n",
                "home/Pictures/terminal.png": "image\n",
                "localappdata/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json": textwrap.dedent(
                    """
                    {
                      // Keep comment support because Windows Terminal uses jsonc.
                      "profiles": {
                        "defaults": {
                          "backgroundImage": "%USERPROFILE%\\\\Pictures\\\\terminal.png",
                        }
                      },
                    }
                    """
                ).strip()
                + "\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, markdown_path, sync_script = self.run_cli(source_home, source_localappdata, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)

        profile_paths = {item["path"] for item in payload["profiles"] if item["exists"]}
        self.assertIn(str(source_home / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"), profile_paths)

        terminal_paths = {item["path"] for item in payload["terminal_settings"] if item["exists"]}
        self.assertIn(
            str(source_localappdata / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"),
            terminal_paths,
        )

        resolved_paths = {item["source_path"] for item in payload["copy_mappings"]}
        self.assertIn(str(source_home / "night-owl.omp.json"), resolved_paths)
        self.assertIn(str(source_home / "Documents" / "WindowsPowerShell" / "aliases.ps1"), resolved_paths)
        self.assertIn(str(source_home / "Pictures" / "terminal.png"), resolved_paths)

        terminal_mapping = next(
            item for item in payload["copy_mappings"]
            if item["source_path"] == str(source_localappdata / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json")
        )
        self.assertEqual(terminal_mapping["target_scope"], "localappdata")

        self.assertIn("posh-git", payload["module_references"])
        self.assertFalse(payload["blockers"], msg=payload["blockers"])
        self.assertIn("## Copy Mappings", markdown_path.read_text(encoding="utf-8"))

        sync_text = sync_script.read_text(encoding="utf-8")
        self.assertIn("[CmdletBinding(SupportsShouldProcess)]", sync_text)
        self.assertIn("TargetHome", sync_text)
        self.assertIn("TargetLocalAppData", sync_text)
        self.assertIn("Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json", sync_text)

    def test_reports_missing_files_and_generates_manual_review_entries(self) -> None:
        source_home, source_localappdata = self.make_source_tree(
            {
                "home/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1": textwrap.dedent(
                    """
                    oh-my-posh init pwsh --config "$HOME\\missing-theme.omp.json" | Invoke-Expression
                    . "C:\\Tools\\custom-shell.ps1"
                    """
                ).strip()
                + "\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, markdown_path, sync_script = self.run_cli(source_home, source_localappdata, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)

        unresolved = payload["unresolved_references"]
        self.assertTrue(unresolved)
        self.assertTrue(any(item["raw_reference"] == "$HOME\\missing-theme.omp.json" for item in unresolved))

        manual_review = payload["manual_review"]
        self.assertTrue(any(item["source_path"] == "C:\\Tools\\custom-shell.ps1" for item in manual_review))
        self.assertTrue(any("No Windows Terminal settings.json file was found." in item for item in payload["blockers"]))

        sync_text = sync_script.read_text(encoding="utf-8")
        self.assertIn("No automatic destination is known", sync_text)
        self.assertIn("## Manual Review", markdown_path.read_text(encoding="utf-8"))

    def test_dedupes_terminal_references_across_repeated_json_values(self) -> None:
        source_home, source_localappdata = self.make_source_tree(
            {
                "home/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1": "Set-Location $HOME\n",
                "home/Pictures/terminal.png": "image\n",
                "localappdata/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json": textwrap.dedent(
                    """
                    {
                      "profiles": {
                        "defaults": {
                          "backgroundImage": "%USERPROFILE%\\\\Pictures\\\\terminal.png"
                        },
                        "list": [
                          {
                            "backgroundImage": "%USERPROFILE%\\\\Pictures\\\\terminal.png"
                          }
                        ]
                      }
                    }
                    """
                ).strip()
                + "\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _, _ = self.run_cli(source_home, source_localappdata, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        image_mappings = [
            item for item in payload["copy_mappings"]
            if item["source_path"] == str(source_home / "Pictures" / "terminal.png")
        ]
        self.assertEqual(len(image_mappings), 1)

    def test_resolves_bare_relative_profile_dependency_in_same_directory(self) -> None:
        source_home, source_localappdata = self.make_source_tree(
            {
                "home/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1": textwrap.dedent(
                    """
                    oh-my-posh init pwsh --config night-owl.omp.json | Invoke-Expression
                    """
                ).strip()
                + "\n",
                "home/Documents/WindowsPowerShell/night-owl.omp.json": "{\n  \"name\": \"night-owl\"\n}\n",
                "localappdata/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json": "{\n  \"profiles\": {}\n}\n",
            }
        )
        output_dir = self.make_output_dir()

        result, json_path, _, _ = self.run_cli(source_home, source_localappdata, output_dir)

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = self.load_json(json_path)
        resolved_paths = {item["source_path"] for item in payload["copy_mappings"]}
        self.assertIn(str(source_home / "Documents" / "WindowsPowerShell" / "night-owl.omp.json"), resolved_paths)
        self.assertFalse(
            any(item["raw_reference"] == "night-owl.omp.json" for item in payload["unresolved_references"])
        )


if __name__ == "__main__":
    unittest.main()
