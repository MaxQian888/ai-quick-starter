from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "screen-recorder" / "scripts" / "record_screen.ps1"


def powershell_executable() -> str | None:
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if exe:
            return exe
    return None


@unittest.skipUnless(powershell_executable(), "PowerShell is required for screen-recorder tests")
class RecordScreenPowerShellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="screen-recorder-ps-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.pwsh = powershell_executable()
        if not self.pwsh:
            self.skipTest("PowerShell not available")

    def run_script(self, *args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )

    def test_capture_window_requires_explicit_window_target(self) -> None:
        result = self.run_script("-Capture", "window", "-DryRun")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires -App, -WindowTitle, or -WindowHandle", result.stderr + result.stdout)

    def test_region_requires_valid_coordinates(self) -> None:
        result = self.run_script("-Capture", "region", "-Region", "10,20,30", "-DryRun")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Region must be x,y,w,h", result.stderr + result.stdout)

    def test_dry_run_uses_ffmpeg_when_present(self) -> None:
        fake_bin = self.temp_dir / "bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        fake_ffmpeg = fake_bin / "ffmpeg.cmd"
        fake_ffmpeg.write_text("@echo off\r\necho fake ffmpeg\r\n", encoding="utf-8")

        result = self.run_script(
            "-Capture",
            "desktop",
            "-DryRun",
            env_overrides={"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"},
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Backend: ffmpeg", result.stdout)
        self.assertIn("Command:", result.stdout)

    def test_dry_run_falls_back_to_psr_when_ffmpeg_missing(self) -> None:
        fake_windir = self.temp_dir / "windir"
        fake_system32 = fake_windir / "System32"
        fake_system32.mkdir(parents=True, exist_ok=True)
        (fake_system32 / "psr.exe").write_text("", encoding="utf-8")

        result = self.run_script(
            "-Capture",
            "desktop",
            "-DryRun",
            env_overrides={"PATH": str(self.temp_dir), "WINDIR": str(fake_windir)},
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Backend: psr", result.stdout)
        self.assertIn("StopAfterSeconds", result.stdout)


if __name__ == "__main__":
    unittest.main()
