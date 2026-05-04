from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
import unittest
import uuid
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "build_e2e_change_plan.py"
)
TMP_ROOT = Path(__file__).resolve().parents[2] / "tmp" / "e2e-test-completer-tests"


class BuildE2eChangePlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dirs: list[Path] = []
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        for path in reversed(self._temp_dirs):
            shutil.rmtree(path, ignore_errors=True)

    def make_temp_dir(self, prefix: str) -> Path:
        root = TMP_ROOT / f"{prefix}-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=False)
        self._temp_dirs.append(root)
        return root

    def make_repo(self, files: dict[str, str]) -> Path:
        root = self.make_temp_dir("e2e-test-completer-repo")
        for relative_path, content in files.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return root

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
        )

    def init_git_repo(self, repo_root: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "config", "user.name", "Codex Tester"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "codex@example.com"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def git_commit_all(self, repo_root: Path, message: str) -> None:
        subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def make_playwright_repo(self) -> Path:
        return self.make_repo(
            {
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "demo-app",
                      "scripts": {
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "playwright.config.ts": "export default {};\n",
                "e2e/auth-login.spec.ts": "// auth login flow\n",
                "e2e/dashboard.spec.ts": "// dashboard flow\n",
                "src/features/auth/login-form.tsx": "export const LoginForm = () => null;\n",
                "src/features/billing/invoice-list.tsx": "export const InvoiceList = () => null;\n",
            }
        )

    def test_discover_mode_detects_playwright_surface(self) -> None:
        repo_root = self.make_playwright_repo()

        result = self.run_cli("--project-root", str(repo_root), "--mode", "discover", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runner"]["framework"], "playwright")
        self.assertEqual(payload["runner"]["package_manager"], "pnpm")
        self.assertEqual(payload["runner"]["primary_command"], "pnpm test:e2e")
        self.assertIn("playwright.config.ts", payload["runner"]["config_paths"])
        self.assertEqual(payload["spec_count"], 2)

    def test_plan_mode_ranks_matching_specs_for_changed_file(self) -> None:
        repo_root = self.make_playwright_repo()

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "plan",
            "--changed-file",
            "src/features/auth/login-form.tsx",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        first_change = payload["change_reports"][0]
        self.assertEqual(first_change["changed_file"], "src/features/auth/login-form.tsx")
        self.assertEqual(first_change["matches"][0]["spec"], "e2e/auth-login.spec.ts")
        self.assertGreater(first_change["matches"][0]["score"], 0)

    def test_plan_mode_flags_unmapped_change_as_coverage_gap(self) -> None:
        repo_root = self.make_playwright_repo()

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "plan",
            "--changed-file",
            "src/features/billing/invoice-list.tsx",
            "--json",
        )

        self.assertEqual(result.returncode, 1, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["overall_status"], "gap")
        self.assertEqual(payload["coverage_gaps"][0]["changed_file"], "src/features/billing/invoice-list.tsx")

    def test_simulate_mode_builds_targeted_playwright_command(self) -> None:
        repo_root = self.make_playwright_repo()

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "simulate",
            "--changed-file",
            "src/features/auth/login-form.tsx",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["overall_status"], "simulated")
        self.assertEqual(
            payload["execution_plan"]["targeted_command"],
            "pnpm exec playwright test e2e/auth-login.spec.ts",
        )
        self.assertEqual(payload["execution_plan"]["full_command"], "pnpm test:e2e")

    def test_discover_mode_detects_cypress_surface(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "shop-app",
                      "scripts": {
                        "e2e": "cypress run"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "package-lock.json": "{}\n",
                "cypress.config.ts": "export default {};\n",
                "cypress/e2e/checkout.cy.ts": "// checkout flow\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "discover", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runner"]["framework"], "cypress")
        self.assertEqual(payload["runner"]["package_manager"], "npm")
        self.assertEqual(payload["runner"]["primary_command"], "npm run e2e")
        self.assertEqual(payload["spec_count"], 1)

    def test_plan_mode_can_match_spec_by_content_tokens(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "demo-app",
                      "scripts": {
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "playwright.config.ts": "export default {};\n",
                "e2e/session.spec.ts": textwrap.dedent(
                    """
                    test("login form allows email sign in", async () => {
                      // login form scenario
                    });
                    """
                ).strip()
                + "\n",
                "src/features/auth/login-form.tsx": "export const LoginForm = () => null;\n",
            }
        )

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "plan",
            "--changed-file",
            "src/features/auth/login-form.tsx",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["change_reports"][0]["matches"][0]["spec"], "e2e/session.spec.ts")
        self.assertIn("content:login", payload["change_reports"][0]["matches"][0]["reasons"])

    def test_discover_mode_detects_nested_playwright_app_surface(self) -> None:
        repo_root = self.make_repo(
            {
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "apps/web/package.json": textwrap.dedent(
                    """
                    {
                      "name": "web-app",
                      "scripts": {
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "apps/web/playwright.config.ts": "export default {};\n",
                "apps/web/e2e/checkout.spec.ts": "// checkout flow\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "discover", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runner"]["framework"], "playwright")
        self.assertEqual(payload["runner"]["working_directory"], "apps/web")
        self.assertEqual(payload["runner"]["primary_command"], "pnpm --dir apps/web test:e2e")

    def test_plan_mode_can_read_changed_files_from_git_base(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "demo-app",
                      "scripts": {
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "playwright.config.ts": "export default {};\n",
                "e2e/auth-login.spec.ts": "// auth login flow\n",
                "src/features/auth/login-form.tsx": "export const LoginForm = () => null;\n",
            }
        )
        self.init_git_repo(repo_root)
        self.git_commit_all(repo_root, "initial")
        (repo_root / "src/features/auth/login-form.tsx").write_text(
            "export const LoginForm = () => 'changed';\n",
            encoding="utf-8",
        )

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "plan",
            "--git-base",
            "HEAD",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("src/features/auth/login-form.tsx", payload["changed_files"])
        self.assertEqual(payload["change_reports"][0]["matches"][0]["spec"], "e2e/auth-login.spec.ts")


    def test_discover_prefers_framework_specific_script_over_generic_e2e_key(self) -> None:
        repo_root = self.make_repo(
            {
                # The generic "e2e" key is listed first and points at cypress.
                # Auto-detection picks playwright (via config file), so the
                # primary command must be the playwright-specific script,
                # not the cypress-flavoured "e2e" entry that happens to
                # collide on the key name.
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "demo-app",
                      "scripts": {
                        "e2e": "cypress run",
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "playwright.config.ts": "export default {};\n",
                "e2e/auth-login.spec.ts": "// auth login flow\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "discover", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runner"]["framework"], "playwright")
        self.assertEqual(payload["runner"]["primary_command"], "pnpm test:e2e")

    def test_plan_mode_handles_git_porcelain_rename_entries(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "demo-app",
                      "scripts": {
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "playwright.config.ts": "export default {};\n",
                "e2e/auth-login.spec.ts": "// auth login flow\n",
                "src/features/auth/legacy-login-form.tsx": "export const LoginForm = () => null;\n",
            }
        )
        self.init_git_repo(repo_root)
        self.git_commit_all(repo_root, "initial")

        # Rename the file via git so porcelain emits an `R  old -> new` entry.
        subprocess.run(
            ["git", "mv", "src/features/auth/legacy-login-form.tsx", "src/features/auth/login-form.tsx"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = self.run_cli(
            "--project-root",
            str(repo_root),
            "--mode",
            "plan",
            "--json",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("src/features/auth/login-form.tsx", payload["changed_files"])
        # The renamed-to file should have been parsed cleanly (no '->' artifact).
        for path in payload["changed_files"]:
            self.assertNotIn("->", path)

    def test_discover_prunes_node_modules_specs_and_packages(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": textwrap.dedent(
                    """
                    {
                      "name": "demo-app",
                      "scripts": {
                        "test:e2e": "playwright test"
                      }
                    }
                    """
                ).strip()
                + "\n",
                "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
                "playwright.config.ts": "export default {};\n",
                "e2e/auth-login.spec.ts": "// auth login flow\n",
                # Vendor-noise files that should never make it into the report.
                "node_modules/some-pkg/package.json": "{}\n",
                "node_modules/some-pkg/playwright.config.ts": "export default {};\n",
                "node_modules/some-pkg/e2e/leaked.spec.ts": "// vendor noise\n",
            }
        )

        result = self.run_cli("--project-root", str(repo_root), "--mode", "discover", "--json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["runner"]["framework"], "playwright")
        self.assertNotIn(
            "node_modules/some-pkg/playwright.config.ts",
            payload["runner"]["config_paths"],
        )
        for spec in payload["spec_paths"]:
            self.assertFalse(spec.startswith("node_modules/"), spec)


if __name__ == "__main__":
    unittest.main()
