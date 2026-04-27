from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "component-reorg-executor" / "scripts" / "apply_component_reorg_plan.py"


class ApplyComponentReorgPlanTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="component-reorg-exec-"))
        for relative_path, content in files.items():
            file_path = temp_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def write_plan(self, repo_root: Path, payload: dict[str, object]) -> Path:
        plan_path = repo_root / "component-plan.json"
        plan_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return plan_path

    def read_output_path(self, stdout: str, key: str) -> Path:
        prefix = f"{key}="
        for line in stdout.splitlines():
            if line.startswith(prefix):
                return Path(line[len(prefix) :].strip())
        self.fail(f"Could not find {key}=... in stdout:\n{stdout}")

    def run_cli_raw(self, plan_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                str(PYTHON),
                str(SCRIPT),
                "--plan",
                str(plan_path),
                *extra_args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result

    def run_cli(self, plan_path: Path, *extra_args: str) -> tuple[dict[str, object], str]:
        result = self.run_cli_raw(plan_path, *extra_args)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        json_path = self.read_output_path(result.stdout, "JSON_OUT")
        markdown_path = self.read_output_path(result.stdout, "MARKDOWN_OUT")
        return json.loads(json_path.read_text(encoding="utf-8")), markdown_path.read_text(encoding="utf-8")

    def test_moves_approved_files_and_rewrites_local_imports(self) -> None:
        repo_root = self.make_repo(
            {
                "src/features/orders/components/OrderPage.tsx": (
                    "import { OrderForm } from './OrderForm';\n"
                    "import { OrderDialog } from './OrderDialog';\n"
                    "export function OrderPage() { return <><OrderForm /><OrderDialog /></>; }\n"
                ),
                "src/features/orders/components/OrderForm.tsx": (
                    "import { useOrderFilters } from './useOrderFilters';\n"
                    "export function OrderForm() { useOrderFilters(); return <form />; }\n"
                ),
                "src/features/orders/components/OrderDialog.tsx": (
                    "import { useOrderFilters } from './useOrderFilters';\n"
                    "export function OrderDialog() { useOrderFilters(); return <dialog />; }\n"
                ),
                "src/features/orders/components/useOrderFilters.ts": "export function useOrderFilters() {}\n",
                "src/features/orders/components/index.ts": (
                    "export * from './OrderForm';\n"
                    "export * from './OrderDialog';\n"
                    "export * from './useOrderFilters';\n"
                ),
            }
        )
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": "src/features/orders/components",
                "move_plan": [
                    {
                        "path": "src/features/orders/components/OrderForm.tsx",
                        "action": "move",
                        "destination_path": "src/features/orders/components/forms/OrderForm.tsx",
                        "proposed_subfolder": "forms",
                    },
                    {
                        "path": "src/features/orders/components/OrderDialog.tsx",
                        "action": "move",
                        "destination_path": "src/features/orders/components/overlays/OrderDialog.tsx",
                        "proposed_subfolder": "overlays",
                    },
                    {
                        "path": "src/features/orders/components/useOrderFilters.ts",
                        "action": "keep-put",
                        "destination_path": "src/features/orders/components/useOrderFilters.ts",
                        "proposed_subfolder": "",
                    },
                    {
                        "path": "src/features/orders/components/index.ts",
                        "action": "keep-put",
                        "destination_path": "src/features/orders/components/index.ts",
                        "proposed_subfolder": "",
                    },
                ],
            },
        )

        payload, _markdown = self.run_cli(plan_path)

        self.assertTrue((repo_root / "src/features/orders/components/forms/OrderForm.tsx").exists())
        self.assertTrue((repo_root / "src/features/orders/components/overlays/OrderDialog.tsx").exists())
        self.assertFalse((repo_root / "src/features/orders/components/OrderForm.tsx").exists())
        self.assertFalse((repo_root / "src/features/orders/components/OrderDialog.tsx").exists())

        page_text = (repo_root / "src/features/orders/components/OrderPage.tsx").read_text(encoding="utf-8")
        self.assertIn("./forms/OrderForm", page_text)
        self.assertIn("./overlays/OrderDialog", page_text)

        moved_form = (repo_root / "src/features/orders/components/forms/OrderForm.tsx").read_text(encoding="utf-8")
        moved_dialog = (repo_root / "src/features/orders/components/overlays/OrderDialog.tsx").read_text(encoding="utf-8")
        self.assertIn("../useOrderFilters", moved_form)
        self.assertIn("../useOrderFilters", moved_dialog)

        barrel_text = (repo_root / "src/features/orders/components/index.ts").read_text(encoding="utf-8")
        self.assertIn("./forms/OrderForm", barrel_text)
        self.assertIn("./overlays/OrderDialog", barrel_text)
        self.assertIn("./useOrderFilters", barrel_text)

        self.assertEqual(payload["summary"]["moved"], 2)
        self.assertGreaterEqual(payload["summary"]["rewritten_files"], 3)

    def test_skips_keep_put_only_plan_without_changes(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/Card.tsx": "export function Card() { return <section />; }\n",
            }
        )
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": "src/components",
                "move_plan": [
                    {
                        "path": "src/components/Card.tsx",
                        "action": "keep-put",
                        "destination_path": "src/components/Card.tsx",
                        "proposed_subfolder": "",
                    }
                ],
            },
        )

        payload, _markdown = self.run_cli(plan_path)

        self.assertEqual(payload["summary"]["moved"], 0)
        self.assertEqual(payload["summary"]["rewritten_files"], 0)
        self.assertTrue((repo_root / "src/components/Card.tsx").exists())

    def test_markdown_contains_required_sections(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/OrderForm.tsx": "export function OrderForm() { return <form />; }\n",
            }
        )
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": "src/components",
                "move_plan": [
                    {
                        "path": "src/components/OrderForm.tsx",
                        "action": "move",
                        "destination_path": "src/components/forms/OrderForm.tsx",
                        "proposed_subfolder": "forms",
                    }
                ],
            },
        )

        _payload, markdown = self.run_cli(plan_path)

        self.assertIn("## Request", markdown)
        self.assertIn("## Applied Moves", markdown)
        self.assertIn("## Rewritten Files", markdown)
        self.assertIn("## Skipped Entries", markdown)

    def test_respects_explicit_output_paths(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/OrderForm.tsx": "export function OrderForm() { return <form />; }\n",
            }
        )
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": "src/components",
                "move_plan": [
                    {
                        "path": "src/components/OrderForm.tsx",
                        "action": "move",
                        "destination_path": "src/components/forms/OrderForm.tsx",
                        "proposed_subfolder": "forms",
                    }
                ],
            },
        )
        json_out = repo_root / "reports" / "execution.json"
        markdown_out = repo_root / "reports" / "execution.md"

        result = self.run_cli_raw(
            plan_path,
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertTrue(json_out.exists(), str(json_out))
        self.assertTrue(markdown_out.exists(), str(markdown_out))
        payload = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["moved"], 1)
        self.assertIn("## Applied Moves", markdown_out.read_text(encoding="utf-8"))

    def test_returns_error_when_planned_move_source_is_missing(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/OrderPage.tsx": "export function OrderPage() { return <div />; }\n",
            }
        )
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": "src/components",
                "move_plan": [
                    {
                        "path": "src/components/Missing.tsx",
                        "action": "move",
                        "destination_path": "src/components/forms/Missing.tsx",
                        "proposed_subfolder": "forms",
                    }
                ],
            },
        )

        result = self.run_cli_raw(plan_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Planned move source does not exist", result.stdout + result.stderr)

    def test_rejects_plan_entries_that_escape_the_repository_root(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/OrderForm.tsx": "export function OrderForm() { return <form />; }\n",
            }
        )
        escaped_dir_name = f"escaped-{repo_root.name}"
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": "src/components",
                "move_plan": [
                    {
                        "path": "src/components/OrderForm.tsx",
                        "action": "move",
                        "destination_path": f"../{escaped_dir_name}/OrderForm.tsx",
                        "proposed_subfolder": "forms",
                    }
                ],
            },
        )

        result = self.run_cli_raw(plan_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must stay within the repository root", result.stdout + result.stderr)
        self.assertTrue((repo_root / "src/components/OrderForm.tsx").exists())
        self.assertFalse((repo_root.parent / escaped_dir_name / "OrderForm.tsx").exists())

    def test_rejects_target_directory_that_escapes_the_repository_root(self) -> None:
        repo_root = self.make_repo(
            {
                "src/components/OrderForm.tsx": "export function OrderForm() { return <form />; }\n",
            }
        )
        escaped_dir_name = f"outside-target-{repo_root.name}"
        plan_path = self.write_plan(
            repo_root,
            {
                "root": str(repo_root),
                "target_directory": f"../{escaped_dir_name}",
                "move_plan": [
                    {
                        "path": "src/components/OrderForm.tsx",
                        "action": "keep-put",
                        "destination_path": "src/components/OrderForm.tsx",
                        "proposed_subfolder": "",
                    }
                ],
            },
        )

        result = self.run_cli_raw(plan_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Target directory must stay within the repository root", result.stdout + result.stderr)
        self.assertFalse((repo_root.parent / escaped_dir_name).exists())


if __name__ == "__main__":
    unittest.main()
