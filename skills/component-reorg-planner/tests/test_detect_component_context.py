from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "component-reorg-planner" / "scripts" / "detect_component_context.py"


class DetectComponentContextTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="component-reorg-context-"))
        for relative_path, content in files.items():
            file_path = temp_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def run_cli(self, repo_root: Path, target: str) -> dict[str, object]:
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
        return json.loads(result.stdout)

    def test_feature_first_target_prefers_feature_local_support_paths(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"dependencies": {"react": "^19.0.0"}}),
                "src/features/orders/components/OrderForm.tsx": "export function OrderForm() { return null; }\n",
                "src/hooks/useTheme.ts": "export function useTheme() {}\n",
            }
        )

        payload = self.run_cli(repo_root, "src/features/orders/components")

        self.assertEqual(payload["framework"], "react")
        self.assertEqual(payload["structure_mode"], "feature-first")
        self.assertEqual(payload["recommended_paths"]["components"], "src/features/orders/components")
        self.assertEqual(payload["recommended_paths"]["hooks"], "src/features/orders/hooks")
        self.assertEqual(payload["recommended_paths"]["utils"], "src/features/orders/utils")

    def test_route_first_target_prefers_route_scoped_support_paths(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"dependencies": {"next": "^16.0.0", "react": "^19.0.0"}}),
                "src/app/orders/page.tsx": "export default function Page() { return null; }\n",
                "src/app/orders/components/OrderSummary.tsx": "export function OrderSummary() { return null; }\n",
            }
        )

        payload = self.run_cli(repo_root, "src/app/orders/components")

        self.assertEqual(payload["framework"], "nextjs")
        self.assertEqual(payload["router"], "app-router")
        self.assertEqual(payload["structure_mode"], "route-first")
        self.assertEqual(payload["recommended_paths"]["components"], "src/app/orders/components")
        self.assertEqual(payload["recommended_paths"]["hooks"], "src/app/orders/hooks")
        self.assertEqual(payload["recommended_paths"]["utils"], "src/app/orders/utils")

    def test_layer_first_target_falls_back_to_source_layers(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps({"dependencies": {"react": "^19.0.0"}}),
                "src/components/admin/UserTable.tsx": "export function UserTable() { return null; }\n",
                "src/hooks/useUsers.ts": "export function useUsers() {}\n",
                "src/utils/formatUser.ts": "export function formatUser() {}\n",
            }
        )

        payload = self.run_cli(repo_root, "src/components/admin")

        self.assertEqual(payload["structure_mode"], "layer-first")
        self.assertEqual(payload["recommended_paths"]["components"], "src/components/admin")
        self.assertEqual(payload["recommended_paths"]["hooks"], "src/hooks")
        self.assertEqual(payload["recommended_paths"]["utils"], "src/utils")
        self.assertEqual(payload["recommended_paths"]["types"], "src/types")


if __name__ == "__main__":
    unittest.main()
