from __future__ import annotations

import argparse
import importlib.util
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT_PATH = WORKSPACE_ROOT / "screenshot" / "scripts" / "take_screenshot.py"
SPEC = importlib.util.spec_from_file_location("take_screenshot_module", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load take_screenshot.py for tests")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)  # type: ignore[union-attr]


@contextmanager
def temporary_env(**kwargs: str):
    original = {key: os.environ.get(key) for key in kwargs}
    try:
        for key, value in kwargs.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TakeScreenshotHelperTests(unittest.TestCase):
    def test_parse_region_accepts_valid_region(self) -> None:
        self.assertEqual(MODULE.parse_region("10,20,300,400"), (10, 20, 300, 400))

    def test_parse_region_rejects_invalid_region(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            MODULE.parse_region("10,20,30")

        with self.assertRaises(argparse.ArgumentTypeError):
            MODULE.parse_region("10,20,-1,100")

    def test_normalize_platform_maps_common_aliases(self) -> None:
        self.assertEqual(MODULE.normalize_platform("mac"), "Darwin")
        self.assertEqual(MODULE.normalize_platform("linux"), "Linux")
        self.assertEqual(MODULE.normalize_platform("win"), "Windows")

    def test_test_mode_enabled_respects_environment_flag(self) -> None:
        with temporary_env(CODEX_SCREENSHOT_TEST_MODE="true"):
            self.assertTrue(MODULE.test_mode_enabled())
        with temporary_env(CODEX_SCREENSHOT_TEST_MODE="false"):
            self.assertFalse(MODULE.test_mode_enabled())

    def test_resolve_output_path_temp_mode_uses_temp_directory(self) -> None:
        out = MODULE.resolve_output_path(None, "temp", "png", "Linux")
        self.assertEqual(out.suffix, ".png")
        self.assertEqual(out.parent, Path(tempfile.gettempdir()))

    def test_multi_output_paths_expands_suffixes(self) -> None:
        base = Path(tempfile.gettempdir()) / "shot.png"
        outputs = MODULE.multi_output_paths(base, ["display-1", "display-2"])
        names = [item.name for item in outputs]
        self.assertEqual(names, ["shot-display-1.png", "shot-display-2.png"])


if __name__ == "__main__":
    unittest.main()
