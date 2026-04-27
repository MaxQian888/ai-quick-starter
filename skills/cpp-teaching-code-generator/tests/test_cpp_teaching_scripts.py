import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

SCAFFOLD_PATH = SCRIPTS_DIR / "scaffold_cpp_lesson.py"
SCAFFOLD_SPEC = importlib.util.spec_from_file_location("scaffold_cpp_lesson", SCAFFOLD_PATH)
SCAFFOLD_MODULE = importlib.util.module_from_spec(SCAFFOLD_SPEC)
assert SCAFFOLD_SPEC.loader is not None
sys.modules[SCAFFOLD_SPEC.name] = SCAFFOLD_MODULE
SCAFFOLD_SPEC.loader.exec_module(SCAFFOLD_MODULE)

BATCH_PATH = SCRIPTS_DIR / "batch_scaffold_cpp_lessons.py"
BATCH_SPEC = importlib.util.spec_from_file_location("batch_scaffold_cpp_lessons", BATCH_PATH)
BATCH_MODULE = importlib.util.module_from_spec(BATCH_SPEC)
assert BATCH_SPEC.loader is not None
sys.modules[BATCH_SPEC.name] = BATCH_MODULE
BATCH_SPEC.loader.exec_module(BATCH_MODULE)


class CppTeachingScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cpp-teaching-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def test_create_lesson_file_writes_compilable_template(self) -> None:
        output = self.temp_dir / "lesson.cpp"

        generated = SCAFFOLD_MODULE.create_lesson_file(
            topic="vector basics",
            level="beginner",
            pattern="concept-demo",
            standard="c++17",
            output_path=output,
            force=False,
        )

        content = generated.read_text(encoding="utf-8")
        self.assertTrue(generated.exists())
        self.assertIn("Topic: vector basics", content)
        self.assertIn("#include <vector>", content)
        self.assertIn("int main()", content)

    def test_parse_text_line_supports_overrides(self) -> None:
        defaults = BATCH_MODULE.LessonSpec(
            topic="",
            level="beginner",
            pattern="guided-implementation",
            standard="c++17",
            output=None,
        )

        spec = BATCH_MODULE.parse_text_line(
            "binary search|advanced|compare-approaches|c++20|search.cpp",
            defaults,
            "topics.txt:1",
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.topic, "binary search")
        self.assertEqual(spec.level, "advanced")
        self.assertEqual(spec.pattern, "compare-approaches")
        self.assertEqual(spec.standard, "c++20")
        self.assertEqual(spec.output, "search.cpp")

    def test_resolve_output_path_uses_unique_suffix_when_needed(self) -> None:
        defaults = BATCH_MODULE.LessonSpec(
            topic="sorting basics",
            level="beginner",
            pattern="guided-implementation",
            standard="c++17",
            output=None,
        )
        used_paths = {self.temp_dir / "sorting_basics.cpp"}

        resolved = BATCH_MODULE.resolve_output_path(
            spec=defaults,
            out_dir=self.temp_dir,
            index=1,
            include_index=False,
            used_paths=used_paths,
        )

        self.assertEqual(resolved, self.temp_dir / "sorting_basics_2.cpp")


if __name__ == "__main__":
    unittest.main()
