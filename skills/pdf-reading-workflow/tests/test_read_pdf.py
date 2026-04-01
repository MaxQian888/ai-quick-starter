from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "read_pdf.py"
SPEC = importlib.util.spec_from_file_location("read_pdf", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeBackend:
    def __init__(self, name: str, capabilities: tuple[str, ...]) -> None:
        self.name = name
        self.capabilities = capabilities


class ReadPdfTests(unittest.TestCase):
    def test_parse_page_spec_handles_ranges_and_deduplicates(self) -> None:
        pages = MODULE.parse_page_spec("1-3, 2, 5, 7-8")
        self.assertEqual(pages, [1, 2, 3, 5, 7, 8])

    def test_parse_page_spec_rejects_descending_ranges(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.parse_page_spec("5-2")

    def test_resolve_pages_uses_full_document_when_range_missing(self) -> None:
        self.assertEqual(MODULE.resolve_pages(None, 4), [1, 2, 3, 4])

    def test_truncate_text_adds_marker(self) -> None:
        value = MODULE.truncate_text("abcdefghij", 5)
        self.assertEqual(value, "abcde\n...[truncated]")

    def test_select_backend_prefers_pymupdf_for_render(self) -> None:
        selected = MODULE.select_backend(
            "render",
            [
                FakeBackend("pdftoppm", ("render",)),
                FakeBackend("pymupdf", ("inspect", "text", "render")),
            ],
        )
        self.assertEqual(selected.name, "pymupdf")

    def test_parse_pdfinfo_output_extracts_keys(self) -> None:
        payload = MODULE.parse_pdfinfo_output("Title: Sample\nPages: 12\n")
        self.assertEqual(payload["Title"], "Sample")
        self.assertEqual(payload["Pages"], "12")

    def test_probe_cli_emits_json_payload(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "probe", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertIn("backends", payload)
        self.assertIn("preferred_backend", payload)


if __name__ == "__main__":
    unittest.main()
