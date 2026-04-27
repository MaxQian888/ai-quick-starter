import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


DETECT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "detect_react_layout.py"
DETECT_SPEC = importlib.util.spec_from_file_location("detect_react_layout", DETECT_PATH)
DETECT_MODULE = importlib.util.module_from_spec(DETECT_SPEC)
assert DETECT_SPEC.loader is not None
sys.modules[DETECT_SPEC.name] = DETECT_MODULE
DETECT_SPEC.loader.exec_module(DETECT_MODULE)

ANALYZE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "analyze_component_split.py"
ANALYZE_SPEC = importlib.util.spec_from_file_location("analyze_component_split", ANALYZE_PATH)
ANALYZE_MODULE = importlib.util.module_from_spec(ANALYZE_SPEC)
assert ANALYZE_SPEC.loader is not None
sys.modules[ANALYZE_SPEC.name] = ANALYZE_MODULE
ANALYZE_SPEC.loader.exec_module(ANALYZE_MODULE)


class ReactSplitScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="react-split-"))
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir, ignore_errors=True))

    def write_file(self, rel_path: str, content: str) -> Path:
        path = self.temp_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_cli(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def test_detect_layout_prefers_feature_first_recommendations(self) -> None:
        self.write_file(
            "package.json",
            json.dumps({"dependencies": {"react": "^19.0.0", "next": "^16.0.0"}}),
        )
        target = self.write_file(
            "src/features/orders/OrdersPage.tsx",
            "export default function OrdersPage() { return null; }\n",
        )
        (self.temp_dir / "src/features/orders/components").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "src/features/orders/hooks").mkdir(parents=True, exist_ok=True)

        package_data = DETECT_MODULE.read_package_json(self.temp_dir)
        source_root = DETECT_MODULE.detect_source_root(self.temp_dir)
        architecture = DETECT_MODULE.detect_architecture(source_root)
        router = DETECT_MODULE.detect_router(self.temp_dir, source_root, DETECT_MODULE.detect_framework(package_data))
        recommendations = DETECT_MODULE.recommend_paths(source_root, architecture, router, target)

        self.assertEqual(architecture, "feature-first")
        self.assertEqual(router, "unknown")
        self.assertEqual(
            Path(recommendations["components"]).resolve(),
            (self.temp_dir / "src/features/orders/components").resolve(),
        )

    def test_analyze_component_builds_high_priority_candidates(self) -> None:
        content = """
export default function OrdersPage() {
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState("idle");
  useEffect(() => {}, []);
  useEffect(() => {}, [count]);
  const formatItem = (value) => value.toUpperCase();
  const buildLabel = (value) => `${value}-${count}`;
  return (
    <section>
      <OrdersTable onClick={() => setCount(count + 1)} />
      <button onClick={() => setStatus("done")}>{buildLabel(formatItem("ok"))}</button>
    </section>
  );
}
""".strip()

        metrics = {
            "jsx_lines": ANALYZE_MODULE.count_jsx_lines(content) + 120,
            "jsx_tag_total": len(ANALYZE_MODULE.JSX_TAG_PATTERN.findall(content)),
            "state_hooks": 3,
            "effect_hooks": 2,
            "data_calls": 0,
            "inline_handlers": 4,
            "helper_functions": ANALYZE_MODULE.count_local_helper_functions(content),
            "type_declarations": 0,
        }
        candidates = ANALYZE_MODULE.build_candidates(
            feature_name="Orders",
            metrics=metrics,
            recommended_dirs={
                "components": "src/features/orders/components",
                "hooks": "src/features/orders/hooks",
                "utils": "src/features/orders/utils",
                "types": "src/features/orders/types",
            },
        )

        kinds = {candidate.kind for candidate in candidates}
        self.assertIn("presentational-extract", kinds)
        self.assertIn("controller-hook-extract", kinds)
        self.assertIn("handler-stabilization", kinds)

    def test_detect_layout_cli_reports_app_router_route_local_recommendations(self) -> None:
        self.write_file(
            "package.json",
            json.dumps({"dependencies": {"react": "^19.0.0", "next": "^16.0.0"}}),
        )
        target = self.write_file(
            "src/app/dashboard/orders/page.tsx",
            "export default function OrdersPage() { return null; }\n",
        )

        result = self.run_cli(
            DETECT_PATH,
            "--root",
            str(self.temp_dir),
            "--target",
            str(target),
            "--pretty",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["router"], "app-router")
        self.assertEqual(
            Path(payload["recommendations"]["components"]).resolve(),
            (self.temp_dir / "src/app/dashboard/orders/components").resolve(),
        )
        self.assertEqual(
            Path(payload["recommendations"]["hooks"]).resolve(),
            (self.temp_dir / "src/app/dashboard/orders/hooks").resolve(),
        )
        self.assertEqual(
            Path(payload["recommendations"]["utils"]).resolve(),
            (self.temp_dir / "src/app/dashboard/orders/utils").resolve(),
        )
        self.assertEqual(
            Path(payload["recommendations"]["types"]).resolve(),
            (self.temp_dir / "src/app/dashboard/orders/types.ts").resolve(),
        )

    def test_analyze_component_cli_uses_layout_json_for_destination_files(self) -> None:
        component_path = self.write_file(
            "src/app/dashboard/orders/page.tsx",
            """
export default function OrdersPage() {
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState("idle");
  const [filter, setFilter] = useState("all");
  useEffect(() => {}, [count]);
  useEffect(() => {}, [status]);
  const formatRow = (value) => value.toUpperCase();
  const buildLabel = (value) => `${value}-${count}`;
  const data = useQuery(["orders"], fetchOrders);
  return (
    <section>
      <header>
        <h1>Orders</h1>
        <p>{status}</p>
      </header>
      <div>
        <span>{filter}</span>
        <span>{count}</span>
        <span>{buildLabel(formatRow("ok"))}</span>
      </div>
      <div>
        <button onClick={() => setFilter("open")}>Open</button>
        <button onClick={() => setFilter("closed")}>Closed</button>
        <button onClick={() => setStatus("done")}>Done</button>
      </div>
      <article>
        <OrdersSummary />
        <OrdersFilters />
        <OrdersCharts />
      </article>
      <OrdersTable onClick={() => setCount(count + 1)} />
      <button onClick={() => setCount(count + 1)}>{buildLabel(formatRow("ok"))}</button>
      <footer>
        <span>{JSON.stringify(data)}</span>
        <span>{JSON.stringify(data)}</span>
        <span>{JSON.stringify(data)}</span>
        <span>{JSON.stringify(data)}</span>
      </footer>
      <pre>{JSON.stringify(data)}</pre>
    </section>
  );
}
            """.strip(),
        )
        layout_path = self.temp_dir / "layout.json"
        layout_path.write_text(
            json.dumps(
                {
                    "recommendations": {
                        "components": "src/app/dashboard/orders/components",
                        "hooks": "src/app/dashboard/orders/hooks",
                        "utils": "src/app/dashboard/orders/utils",
                        "types": "src/app/dashboard/orders/types.ts",
                    }
                }
            ),
            encoding="utf-8",
        )

        result = self.run_cli(
            ANALYZE_PATH,
            "--file",
            str(component_path),
            "--layout-json",
            str(layout_path),
            "--pretty",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        suggested_files = {candidate["suggested_file"].replace("\\", "/") for candidate in payload["candidates"]}
        self.assertIn("src/app/dashboard/orders/hooks/useOrdersController.ts", suggested_files)
        self.assertIn("src/app/dashboard/orders/hooks/useOrdersData.ts", suggested_files)
        self.assertIn("src/app/dashboard/orders/utils/orders.utils.ts", suggested_files)
        self.assertIn("src/app/dashboard/orders/hooks/useOrdersHandlers.ts", suggested_files)


if __name__ == "__main__":
    unittest.main()
