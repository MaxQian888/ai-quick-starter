from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "remotion" / "scripts" / "download-stitch-asset.sh"


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


def make_fake_curl(bin_dir: Path) -> None:
    payload = """#!/usr/bin/env bash
out=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o)
      out="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [ -n "${FAKE_CURL_PAYLOAD:-}" ] && [ -n "$out" ]; then
  printf "%s" "$FAKE_CURL_PAYLOAD" > "$out"
fi
exit "${FAKE_CURL_EXIT_CODE:-0}"
"""
    curl_path = bin_dir / "curl"
    curl_path.write_text(payload, encoding="utf-8", newline="\n")
    curl_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


@unittest.skipUnless(bash_works(), "working bash runtime is required for shell script tests")
class DownloadStitchAssetScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="remotion-download-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.bin_dir = self.temp_dir / "bin"
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        make_fake_curl(self.bin_dir)

    def run_script(self, *args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PATH"] = f"{self.bin_dir}{os.pathsep}{env.get('PATH', '')}"
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_requires_two_arguments(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Usage:", result.stdout)

    def test_success_download_creates_output_path(self) -> None:
        output_file = self.temp_dir / "assets" / "screen.png"
        result = self.run_script(
            "https://example.test/screen.png",
            str(output_file),
            env_overrides={"FAKE_CURL_EXIT_CODE": "0", "FAKE_CURL_PAYLOAD": "PNGDATA"},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(output_file.exists())
        self.assertEqual(output_file.read_text(encoding="utf-8"), "PNGDATA")
        self.assertIn("Successfully downloaded", result.stdout)

    def test_failure_download_returns_non_zero(self) -> None:
        output_file = self.temp_dir / "assets" / "screen.png"
        result = self.run_script(
            "https://example.test/screen.png",
            str(output_file),
            env_overrides={"FAKE_CURL_EXIT_CODE": "22"},
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
