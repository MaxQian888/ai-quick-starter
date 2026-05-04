import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "component_test_map.py"
SPEC = importlib.util.spec_from_file_location("component_test_map", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ComponentTestMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="component-test-map-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def write_file(self, rel_path: str, content: str = "") -> None:
        path = self.temp_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def audit(self):
        return MODULE.audit_mappings(
            root=self.temp_dir,
            component_exts=MODULE.DEFAULT_COMPONENT_EXTS,
            test_exts=MODULE.DEFAULT_TEST_EXTS,
            exclude_dirs=MODULE.DEFAULT_EXCLUDE_DIRS,
        )

    def test_audit_mappings_detects_missing_and_orphans(self) -> None:
        self.write_file("src/Button.tsx", "export const Button = () => null;\n")
        self.write_file("src/Card.tsx", "export const Card = () => null;\n")
        self.write_file("src/Button.test.tsx", "test('Button', () => {});\n")
        self.write_file("tests/orphan.test.tsx", "test('orphan', () => {});\n")

        results, missing, orphan_tests = self.audit()

        mapped = {result.component.as_posix(): [item.as_posix() for item in result.matched_tests] for result in results}
        self.assertIn("src/Button.tsx", mapped)
        self.assertEqual(mapped["src/Button.tsx"], ["src/Button.test.tsx"])
        self.assertIn(Path("src/Card.tsx"), missing)
        self.assertIn(Path("tests/orphan.test.tsx"), orphan_tests)

    def test_maybe_scaffold_missing_creates_expected_test_file(self) -> None:
        self.write_file("src/widgets/Panel.tsx", "export const Panel = () => null;\n")

        created = MODULE.maybe_scaffold_missing(
            root=self.temp_dir,
            missing_components=[Path("src/widgets/Panel.tsx")],
            test_exts=MODULE.DEFAULT_TEST_EXTS,
            force=False,
        )

        self.assertEqual(created, [Path("src/widgets/Panel.test.tsx")])
        scaffold_path = self.temp_dir / "src/widgets/Panel.test.tsx"
        self.assertTrue(scaffold_path.exists())
        contents = scaffold_path.read_text(encoding="utf-8")
        self.assertIn('describe("Panel"', contents)
        # Scaffold must NOT silently pass — it.todo keeps the test pending.
        self.assertIn("it.todo", contents)
        self.assertNotIn("expect(true).toBe(true)", contents)

    def test_index_pattern_maps_to_parent_named_test(self) -> None:
        self.write_file("src/Modal/index.tsx", "export default () => null;\n")
        self.write_file("src/Modal/Modal.test.tsx", "test('Modal', () => {});\n")

        results, missing, orphan_tests = self.audit()

        mapped = {r.component.as_posix(): [t.as_posix() for t in r.matched_tests] for r in results}
        self.assertEqual(mapped["src/Modal/index.tsx"], ["src/Modal/Modal.test.tsx"])
        self.assertEqual(missing, [])
        self.assertEqual(orphan_tests, [])

    def test_index_pattern_scaffold_uses_parent_directory_name(self) -> None:
        self.write_file("src/Drawer/index.tsx", "export default () => null;\n")
        scaffold = MODULE.render_scaffold(Path("src/Drawer/index.tsx"))
        self.assertIn('describe("Drawer"', scaffold)

    def test_duplicate_tests_are_detected(self) -> None:
        self.write_file("src/List.tsx", "export const List = () => null;\n")
        self.write_file("src/List.test.tsx", "test('List', () => {});\n")
        self.write_file("src/__tests__/List.test.tsx", "test('List again', () => {});\n")

        results, _missing, _orphans = self.audit()
        duplicates = [r for r in results if len(r.matched_tests) > 1]

        self.assertEqual(len(duplicates), 1)
        names = sorted(t.as_posix() for t in duplicates[0].matched_tests)
        self.assertEqual(
            names,
            ["src/List.test.tsx", "src/__tests__/List.test.tsx"],
        )

    def test_default_excludes_skip_e2e_and_storybook(self) -> None:
        self.write_file("src/Real.tsx", "export const Real = () => null;\n")
        self.write_file("src/Real.test.tsx", "test('Real', () => {});\n")
        self.write_file("e2e/Flow.tsx", "// fake")
        self.write_file("storybook-static/Foo.tsx", "// fake")
        self.write_file("__mocks__/api.ts", "// fake")

        results, missing, orphan_tests = self.audit()
        components = {r.component.as_posix() for r in results}

        self.assertEqual(components, {"src/Real.tsx"})
        self.assertEqual(missing, [])
        self.assertEqual(orphan_tests, [])

    def test_detect_framework_reads_package_json(self) -> None:
        self.write_file(
            "package.json",
            json.dumps({"devDependencies": {"jest": "^29.0.0"}}),
        )
        self.assertEqual(MODULE.detect_framework(self.temp_dir), "jest")

        # vitest takes precedence when both appear.
        self.write_file(
            "package.json",
            json.dumps({"devDependencies": {"jest": "^29", "vitest": "^1"}}),
        )
        self.assertEqual(MODULE.detect_framework(self.temp_dir), "vitest")

        # No package.json at all.
        empty = Path(tempfile.mkdtemp(prefix="no-pkg-"))
        self.addCleanup(lambda: shutil.rmtree(empty, ignore_errors=True))
        self.assertEqual(MODULE.detect_framework(empty), "unknown")

    def test_jest_scaffold_omits_vitest_import(self) -> None:
        scaffold = MODULE.render_scaffold(Path("src/Foo.tsx"), framework="jest")
        self.assertNotIn('from "vitest"', scaffold)
        self.assertIn("Jest globals", scaffold)


if __name__ == "__main__":
    unittest.main()
