from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "shadcn-ui" / "scripts" / "verify-setup.ps1"


def powershell_executable() -> str | None:
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if exe:
            return exe
    return None


@unittest.skipUnless(powershell_executable(), "PowerShell is required for script tests")
class VerifySetupPowerShellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="shadcn-verify-ps-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.pwsh = powershell_executable()
        if not self.pwsh:
            self.skipTest("PowerShell not found")

    def run_script(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=self.temp_dir,
            check=False,
        )

    def test_fails_without_components_json(self) -> None:
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("components.json not found", result.stdout)

    def test_passes_minimum_setup(self) -> None:
        (self.temp_dir / "components.json").write_text("{}", encoding="utf-8")
        (self.temp_dir / "tailwind.config.js").write_text("module.exports = {}", encoding="utf-8")
        (self.temp_dir / "src" / "components" / "ui").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "src" / "index.css").write_text(
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n:root { --background: 0 0% 100%; }\n",
            encoding="utf-8",
        )
        (self.temp_dir / "src" / "lib").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "src" / "lib" / "utils.ts").write_text(
            "export function cn(...inputs: string[]) { return inputs.join(' '); }\n",
            encoding="utf-8",
        )

        result = self.run_script()
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Setup verification complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
