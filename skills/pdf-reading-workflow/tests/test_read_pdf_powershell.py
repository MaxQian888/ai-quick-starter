from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "pdf-reading-workflow" / "scripts" / "read_pdf.ps1"


def powershell_executable() -> str | None:
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if exe:
            return exe
    return None


@unittest.skipUnless(powershell_executable(), "PowerShell is required for pdf-reading-workflow tests")
class ReadPdfPowerShellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pwsh = powershell_executable()
        if not self.pwsh:
            self.skipTest("PowerShell not available")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pdf-reading-workflow-ps-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            cwd=str(self.temp_dir),
        )

    def test_probe_json_is_forwarded_through_wrapper(self) -> None:
        result = self.run_script("probe", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertIn("backends", payload)
        self.assertIn("preferred_backend", payload)

    def test_missing_pdf_error_is_forwarded_through_wrapper(self) -> None:
        result = self.run_script("inspect", str(self.temp_dir / "missing.pdf"))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PDF not found", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
