from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPTS_DIR = WORKSPACE_ROOT / "powershell-writing-assistant" / "scripts"


def powershell_executable() -> str | None:
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if exe:
            return exe
    return None


@unittest.skipUnless(powershell_executable(), "PowerShell is required for powershell-writing-assistant tests")
class PowerShellWritingAssistantPythonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pwsh-writing-assistant-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.pwsh = powershell_executable()
        if not self.pwsh:
            self.skipTest("PowerShell not available")

    def run_script(self, script_name: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPTS_DIR / script_name), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=cwd or self.temp_dir,
        )

    def test_advanced_function_template_supports_pipeline_and_should_process(self) -> None:
        output_path = self.temp_dir / "Get-DemoItem.ps1"
        result = self.run_script(
            "new-advanced-function-template.ps1",
            "-Name",
            "Get-DemoItem",
            "-OutputPath",
            str(output_path),
            "-SupportsShouldProcess",
            "-AcceptPipelineInput",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("SupportsShouldProcess", content)
        self.assertIn("ValueFromPipeline", content)
        self.assertIn("function Get-DemoItem", content)

    def test_module_template_generates_manifest_module_and_test(self) -> None:
        modules_root = self.temp_dir / "modules"
        result = self.run_script(
            "new-module-template.ps1",
            "-ModuleName",
            "ContosoTools",
            "-RootPath",
            str(modules_root),
            "-Functions",
            "Get-ContosoStatus,Set-ContosoStatus",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        module_dir = modules_root / "ContosoTools"
        self.assertTrue((module_dir / "ContosoTools.psm1").exists())
        self.assertTrue((module_dir / "ContosoTools.psd1").exists())
        self.assertTrue((module_dir / "Tests" / "Get-ContosoStatus.Tests.ps1").exists())

    def test_quality_gate_passes_valid_script_and_fails_invalid_script(self) -> None:
        valid_script = self.temp_dir / "Get-ValidItem.ps1"
        valid_script.write_text(
            "function Get-ValidItem {\n    [CmdletBinding()]\n    param()\n    process { [pscustomobject]@{ Ok = $true } }\n}\n",
            encoding="utf-8",
        )
        invalid_script = self.temp_dir / "Get-BrokenItem.ps1"
        invalid_script.write_text("function Get-BrokenItem {\n    param(\n}\n", encoding="utf-8")

        valid_result = self.run_script(
            "invoke-pwsh-quality-gate.ps1",
            "-Path",
            str(valid_script),
        )
        self.assertEqual(valid_result.returncode, 0, msg=valid_result.stderr or valid_result.stdout)
        self.assertIn("PowerShell quality gate passed", valid_result.stdout)

        invalid_result = self.run_script(
            "invoke-pwsh-quality-gate.ps1",
            "-Path",
            str(invalid_script),
        )
        self.assertNotEqual(invalid_result.returncode, 0)
        self.assertIn("[ERROR]", invalid_result.stdout)


if __name__ == "__main__":
    unittest.main()
