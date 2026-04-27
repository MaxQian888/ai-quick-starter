from __future__ import annotations

import http.server
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT = WORKSPACE_ROOT / "react-components" / "scripts" / "fetch-stitch.ps1"


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
class FetchStitchPowerShellTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="react-components-fetch-ps-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))
        self.pwsh = powershell_executable()
        if not self.pwsh:
            self.skipTest("PowerShell not found")

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [self.pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPT), *args]
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_requires_arguments(self) -> None:
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cannot process command", result.stderr + result.stdout)

    def test_fetch_success(self) -> None:
        source_dir = self.temp_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        output_path = self.temp_dir / "out" / "index.html"

        with static_server(source_dir) as base_url:
            result = self.run_script(f"{base_url}/index.html", str(output_path))

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_text(encoding="utf-8"), "<html>ok</html>")
        self.assertIn("Successfully retrieved HTML", result.stdout)

    def test_fetch_failure(self) -> None:
        output_path = self.temp_dir / "out" / "index.html"
        result = self.run_script("http://127.0.0.1:9/does-not-exist.html", str(output_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Failed to retrieve content", result.stdout)


if __name__ == "__main__":
    unittest.main()
