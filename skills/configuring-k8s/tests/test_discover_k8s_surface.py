from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
PYTHON = WORKSPACE_ROOT / ".uv-python" / "cpython-3.11.15-windows-x86_64-none" / "python.exe"
SCRIPT = WORKSPACE_ROOT / "configuring-k8s" / "scripts" / "discover_k8s_surface.py"
FIXTURES = WORKSPACE_ROOT / "configuring-k8s" / "tests" / "fixtures"


class DiscoverK8sSurfaceTests(unittest.TestCase):
    def run_cli(self, fixture_name: str) -> dict[str, object]:
        repo_root = FIXTURES / fixture_name
        result = subprocess.run(
            [str(PYTHON), str(SCRIPT), "--project-root", str(repo_root), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_detects_helm_chart_and_values(self) -> None:
        payload = self.run_cli("helm-chart")

        toolchains = {item["name"] for item in payload["toolchains"]}
        self.assertIn("helm", toolchains)
        entry_paths = [item["path"] for item in payload["entrypoints"]]
        self.assertIn("charts/app/Chart.yaml", entry_paths)
        file_types = {item["path"]: item["type"] for item in payload["files"]}
        self.assertEqual(file_types["charts/app/values-prod.yaml"], "helm-values")

    def test_detects_kustomize_and_manifest_metadata(self) -> None:
        payload = self.run_cli("kustomize-base")

        entry_kinds = {item["path"]: item["kind"] for item in payload["entrypoints"]}
        self.assertEqual(entry_kinds["deploy/base/kustomization.yaml"], "kustomization")
        deployment = next(item for item in payload["files"] if item["path"] == "deploy/base/deployment.yaml")
        self.assertEqual(deployment["kind"], "Deployment")
        self.assertEqual(deployment["namespace"], "staging")

    def test_detects_secret_risk_and_skips_tmp(self) -> None:
        payload = self.run_cli("secret-only")

        self.assertTrue(any("Secret-bearing" in risk for risk in payload["risks"]))
        paths = [item["path"] for item in payload["files"]]
        self.assertIn("service/secret.yaml", paths)
        self.assertNotIn("tmp/ignored/Chart.yaml", paths)

    def test_detects_helmfile_entrypoint(self) -> None:
        payload = self.run_cli("helmfile-repo")

        toolchains = {item["name"] for item in payload["toolchains"]}
        self.assertIn("helmfile", toolchains)
        entry = next(item for item in payload["entrypoints"] if item["path"] == "helmfile.yaml")
        self.assertEqual(entry["kind"], "helmfile")

    def test_detects_named_kubeconfig_file(self) -> None:
        payload = self.run_cli("kubeconfig-repo")

        toolchains = {item["name"] for item in payload["toolchains"]}
        self.assertIn("kubeconfig", toolchains)
        record = next(item for item in payload["files"] if item["path"] == "configs/prod.kubeconfig")
        self.assertEqual(record["type"], "kubeconfig")


if __name__ == "__main__":
    unittest.main()
