from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


def load_module(module_name: str, relative_script_path: str):
    script_path = Path(__file__).resolve().parents[1] / relative_script_path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sync_change_tasks = load_module("openspec_sync_change_tasks", "scripts/sync_change_tasks.py")


class SyncChangeTasksTests(unittest.TestCase):
    def test_updates_checkbox_and_inserts_detail_note(self) -> None:
        original = (
            "# Tasks\n\n"
            "- [ ] Inspect current implementation\n"
            "- [ ] Refresh tasks and notes\n"
        )
        instructions = {
            "task_updates": [
                {
                    "match": "Inspect current implementation",
                    "checked": True,
                    "detail": "Compared the implementation against current OpenSpec artifacts.",
                }
            ]
        }

        updated = sync_change_tasks.apply_task_updates(original, instructions)

        self.assertIn("- [x] Inspect current implementation", updated)
        self.assertIn("Compared the implementation against current OpenSpec artifacts.", updated)

    def test_missing_task_match_raises_clear_error(self) -> None:
        original = "# Tasks\n\n- [ ] Existing task\n"
        instructions = {"task_updates": [{"match": "Missing task", "checked": True}]}

        with self.assertRaisesRegex(ValueError, "Missing task"):
            sync_change_tasks.apply_task_updates(original, instructions)

    def test_append_sections_adds_or_extends_named_section(self) -> None:
        original = "# Tasks\n\n- [ ] Existing task\n"
        instructions = {
            "append_sections": [
                {
                    "heading": "Implementation Notes",
                    "lines": [
                        "- Validation still blocks archive because specs are incomplete.",
                        "- Archive history was preserved pending human review.",
                    ],
                }
            ]
        }

        updated = sync_change_tasks.apply_task_updates(original, instructions)

        self.assertIn("## Implementation Notes", updated)
        self.assertIn("Archive history was preserved pending human review.", updated)


if __name__ == "__main__":
    unittest.main()
