from __future__ import annotations

import http.server
import socketserver
import subprocess
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
import shutil


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "remotion" / "scripts" / "download-stitch-asset.py"


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


class DownloadStitchAssetPythonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="remotion-download-py-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(PYTHON), str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_requires_arguments(self) -> None:
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage:", (result.stderr or "").lower())

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
