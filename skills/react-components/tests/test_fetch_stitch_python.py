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
SCRIPT = WORKSPACE_ROOT / "react-components" / "scripts" / "fetch-stitch.py"


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


class FetchStitchPythonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="react-components-fetch-py-"))
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
        result = self.run_script("http://127.0.0.1:9/missing.html", str(output_path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Failed to retrieve content", result.stdout)


if __name__ == "__main__":
    unittest.main()
