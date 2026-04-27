import importlib.util
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "plan_split.py"
SPEC = importlib.util.spec_from_file_location("plan_split", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PlanSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="plan-split-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def write_file(self, rel_path: str, content: str) -> Path:
        path = self.temp_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_detect_style_prefers_hexagonal_markers(self) -> None:
        for folder in ("src/domain", "src/application", "src/infrastructure"):
            (self.temp_dir / folder).mkdir(parents=True, exist_ok=True)

        style, reason = MODULE.detect_style(self.temp_dir, "auto")

        self.assertEqual(style, "hexagonal")
        self.assertIn("domain/application/infrastructure", reason)

    def test_build_plan_groups_symbols_into_expected_files(self) -> None:
        target = self.write_file(
            "src/orders/order_service.py",
            """
import requests

class OrderService:
    pass

class OrderRepository:
    pass

def get_order():
    return 1

SETTINGS = {"debug": True}
""".strip(),
        )
        package_dir = target.parent / "order_service_parts"
        imports, symbols = MODULE.extract_symbols(target)

        plan = MODULE.build_plan(
            project_root=self.temp_dir,
            target=target,
            package_dir=package_dir,
            style="layered",
            style_reason="test",
            imports=imports,
            symbols=symbols,
        )

        file_paths = {item["path"] for item in plan["files"]}
        self.assertIn("src/orders/order_service_parts/services.py", file_paths)
        self.assertIn("src/orders/order_service_parts/repositories.py", file_paths)
        self.assertIn("src/orders/order_service_parts/config.py", file_paths)
        self.assertIn("requests", plan["import_dependencies"])

    def test_create_scaffold_writes_placeholder_modules(self) -> None:
        target = self.write_file(
            "src/orders/order_service.py",
            "def get_order():\n    return 1\n",
        )
        plan = {
            "target_package": "src/orders/order_service_parts",
            "files": [
                {
                    "path": "src/orders/order_service_parts/services.py",
                    "symbols": [
                        {"name": "get_order", "kind": "function", "line": 1, "bucket": "services"}
                    ],
                }
            ],
        }

        created = MODULE.create_scaffold(plan, self.temp_dir)

        self.assertIn("src/orders/order_service_parts/__init__.py", created)
        self.assertIn("src/orders/order_service_parts/services.py", created)
        placeholder = self.temp_dir / "src/orders/order_service_parts/services.py"
        self.assertTrue(placeholder.exists())
        self.assertIn("get_order", placeholder.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
