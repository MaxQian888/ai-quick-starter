from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "component-reorg-planner" / "scripts" / "build_component_reorg_plan.py"


class BuildComponentReorgPlanTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="component-reorg-plan-"))
        for relative_path, content in files.items():
            file_path = temp_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def run_cli(self, repo_root: Path, target: str) -> tuple[dict[str, object], str]:
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--root",
                str(repo_root),
                "--target",
                target,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        json_path = self.read_output_path(result.stdout, "JSON_OUT")
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        return json.loads(json_path.read_text(encoding="utf-8")), markdown_path.read_text(encoding="utf-8")

    def test_plans_functional_groups_and_keeps_support_files_put(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"dependencies": {"react": "^19.0.0"}}),
                "src/features/orders/components/OrderForm.tsx": "export function OrderForm() { return <form />; }\n",
                "src/features/orders/components/OrderField.tsx": "export function OrderField() { return <input />; }\n",
                "src/features/orders/components/OrdersTable.tsx": "export function OrdersTable() { return <table />; }\n",
                "src/features/orders/components/useOrderFilters.ts": "export function useOrderFilters() {}\n",
                "src/features/orders/components/index.ts": "export * from './OrderForm';\n",
            }
        )

        payload, _markdown = self.run_cli(repo_root, "src/features/orders/components")

        subfolders = {entry["name"] for entry in payload["proposed_subfolders"]}
        self.assertIn("forms", subfolders)
        self.assertIn("data-display", subfolders)

        move_plan = {entry["path"]: entry for entry in payload["move_plan"]}
        self.assertEqual(move_plan["src/features/orders/components/OrderForm.tsx"]["action"], "move")
        self.assertEqual(move_plan["src/features/orders/components/OrderForm.tsx"]["proposed_subfolder"], "forms")
        self.assertEqual(move_plan["src/features/orders/components/OrdersTable.tsx"]["proposed_subfolder"], "data-display")
        self.assertEqual(move_plan["src/features/orders/components/useOrderFilters.ts"]["action"], "keep-put")
        self.assertEqual(move_plan["src/features/orders/components/index.ts"]["action"], "keep-put")

    def test_low_confidence_names_block_speculative_moves(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"dependencies": {"react": "^19.0.0"}}),
                "src/components/Card.tsx": "export function Card() { return <section />; }\n",
                "src/components/Panel.tsx": "export function Panel() { return <section />; }\n",
            }
        )

        payload, _markdown = self.run_cli(repo_root, "src/components")

        self.assertEqual(payload["summary"]["move_candidates"], 0)
        self.assertFalse(payload["proposed_subfolders"])
        self.assertTrue(any("low-confidence" in item for item in payload["forbidden_moves"]))
        self.assertTrue(all(entry["action"] == "keep-put" for entry in payload["move_plan"]))

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"dependencies": {"next": "^16.0.0", "react": "^19.0.0"}}),
                "src/app/orders/page.tsx": "export default function Page() { return null; }\n",
                "src/app/orders/components/OrderDialog.tsx": "export function OrderDialog() { return <dialog />; }\n",
            }
        )

        _payload, markdown = self.run_cli(repo_root, "src/app/orders/components")

        self.assertIn("## Project Context", markdown)
        self.assertIn("## Proposed Functional Subfolders", markdown)
        self.assertIn("## Move Plan", markdown)
        self.assertIn("## Forbidden Moves", markdown)


if __name__ == "__main__":
    unittest.main()
