from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "shadcn-ui" / "scripts" / "verify-setup.sh"


def bash_works() -> bool:
    if not shutil.which("bash"):
        return False
    try:
        proc = subprocess.run(
            ["bash", "-lc", "echo codex-bash-ok"],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0 and "codex-bash-ok" in (proc.stdout or "")
    except OSError:
        return False


@unittest.skipUnless(bash_works(), "working bash runtime is required for shell script tests")
class VerifySetupScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="shadcn-verify-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def run_script(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=self.temp_dir,
            check=False,
        )

    def test_fails_when_components_json_is_missing(self) -> None:
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("components.json not found", result.stdout)

    def test_passes_minimal_setup(self) -> None:
        (self.temp_dir / "components.json").write_text("{}", encoding="utf-8")
        (self.temp_dir / "tailwind.config.js").write_text("module.exports = {}", encoding="utf-8")
        (self.temp_dir / "src").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "src" / "index.css").write_text(
            "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n:root { --background: 0 0% 100%; }\n",
            encoding="utf-8",
        )

        result = self.run_script()
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Setup verification complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
