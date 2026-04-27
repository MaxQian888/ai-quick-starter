from __future__ import annotations

import http.server
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "remotion" / "scripts" / "download-stitch-asset.ps1"


def powershell_executable() -> str | None:
    for name in ("pwsh", "powershell"):
        exe = shutil.which(name)
        if exe:
            return exe
    return None


@contextmanager
def static_server(root: Path):
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(root), **kwargs)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()
            thread.join(timeout=2)


@unittest.skipUnless(powershell_executable(), "PowerShell is required for script tests")
class DownloadStitchAssetPowerShellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="remotion-download-ps-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.pwsh = powershell_executable()
        if not self.pwsh:
            self.skipTest("PowerShell not found")

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_requires_arguments(self) -> None:
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)

    def test_download_success(self) -> None:
        source_dir = self.temp_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "asset.png").write_bytes(b"PNGDATA")
        output_path = self.temp_dir / "assets" / "asset.png"

        with static_server(source_dir) as base_url:
            result = self.run_script(f"{base_url}/asset.png", str(output_path))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_bytes(), b"PNGDATA")
        self.assertIn("Successfully downloaded", result.stdout)

    def test_download_failure(self) -> None:
        output_path = self.temp_dir / "assets" / "asset.png"
        result = self.run_script("http://127.0.0.1:9/asset.png", str(output_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Download failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
