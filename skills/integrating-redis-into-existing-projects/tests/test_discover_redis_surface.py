from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "discover_redis_surface.py"
)


class DiscoverRedisSurfaceTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="redis-skill-"))
        for relative_path, content in files.items():
            file_path = temp_dir / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return temp_dir

    def run_cli(self, repo_root: Path) -> dict[str, object]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--project-root",
            str(repo_root),
            "--json",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def dependency_names(self, payload: dict[str, object]) -> set[str]:
        dependencies = payload["redis_dependencies"]
        assert isinstance(dependencies, list)
        return {item["name"] for item in dependencies}

    def config_paths(self, payload: dict[str, object]) -> set[str]:
        config_files = payload["config_files"]
        assert isinstance(config_files, list)
        return {item["path"] for item in config_files}

    def candidate_paths(self, payload: dict[str, object], kind: str) -> list[str]:
        integration_candidates = payload["integration_candidates"]
        assert isinstance(integration_candidates, dict)
        bucket = integration_candidates.get(kind, [])
        assert isinstance(bucket, list)
        return [item["path"] for item in bucket]

    def test_node_repo_highlights_session_and_queue_seams(self) -> None:
        repo_root = self.make_repo(
            {
                "package.json": json.dumps(
                    {
                        "name": "demo",
                        "dependencies": {
                            "next": "15.0.0",
                            "express": "4.21.0",
                            "express-session": "1.18.0",
                            "bullmq": "5.0.0",
                        },
                    }
                ),
                ".env.example": "REDIS_URL=redis://localhost:6379\n",
                "src/server.ts": (
                    'import session from "express-session";\n'
                    'import { Queue } from "bullmq";\n'
                    "app.use(session({ secret: process.env.SESSION_SECRET }));\n"
                    'const emailQueue = new Queue("emails");\n'
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertIn("node", payload["stacks"])
        self.assertIn("nextjs", payload["frameworks"])
        self.assertIn("express", payload["frameworks"])
        self.assertIn("bullmq", self.dependency_names(payload))
        self.assertIn(".env.example", self.config_paths(payload))
        self.assertIn("src/server.ts", self.candidate_paths(payload, "session"))
        self.assertIn("src/server.ts", self.candidate_paths(payload, "queue"))
        self.assertTrue(
            any(
                "dedicated Redis client" in item
                for item in payload["recommendations"]
            )
        )

    def test_python_repo_highlights_cache_and_rate_limit_signals(self) -> None:
        repo_root = self.make_repo(
            {
                "pyproject.toml": (
                    "[project]\n"
                    "name = 'demo'\n"
                    "dependencies = [\n"
                    "  'fastapi>=0.111',\n"
                    "  'redis>=5.0',\n"
                    "  'celery>=5.4',\n"
                    "]\n"
                ),
                ".env": "REDIS_URL=redis://localhost:6379/0\n",
                "app/main.py": (
                    "from fastapi import FastAPI\n"
                    "from redis import Redis\n"
                    "from celery import Celery\n"
                    "from slowapi import Limiter\n"
                    "cache = Redis.from_url('redis://localhost:6379/0')\n"
                    "celery_app = Celery(__name__)\n"
                    "limiter = Limiter(key_func=lambda request: request.client.host)\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertIn("python", payload["stacks"])
        self.assertIn("fastapi", payload["frameworks"])
        self.assertIn("redis", self.dependency_names(payload))
        self.assertIn("celery", self.dependency_names(payload))
        self.assertIn(".env", self.config_paths(payload))
        self.assertIn("app/main.py", self.candidate_paths(payload, "cache"))
        self.assertIn("app/main.py", self.candidate_paths(payload, "queue"))
        self.assertIn("app/main.py", self.candidate_paths(payload, "rate_limit"))

    def test_spring_repo_detects_redis_dependencies_and_config(self) -> None:
        repo_root = self.make_repo(
            {
                "pom.xml": (
                    "<project>"
                    "<dependencies>"
                    "<dependency><artifactId>spring-boot-starter-web</artifactId></dependency>"
                    "<dependency><artifactId>spring-boot-starter-data-redis</artifactId></dependency>"
                    "<dependency><artifactId>spring-session-data-redis</artifactId></dependency>"
                    "</dependencies>"
                    "</project>"
                ),
                "src/main/resources/application.yml": (
                    "spring:\n"
                    "  data:\n"
                    "    redis:\n"
                    "      host: localhost\n"
                    "  session:\n"
                    "    store-type: redis\n"
                ),
                "src/main/java/com/example/DemoApplication.java": (
                    "@SpringBootApplication\n"
                    "@EnableCaching\n"
                    "public class DemoApplication {}\n"
                ),
            }
        )

        payload = self.run_cli(repo_root)

        self.assertIn("java", payload["stacks"])
        self.assertIn("spring", payload["frameworks"])
        self.assertIn("spring-boot-starter-data-redis", self.dependency_names(payload))
        self.assertIn("spring-session-data-redis", self.dependency_names(payload))
        self.assertIn(
            "src/main/resources/application.yml",
            self.config_paths(payload),
        )
        self.assertIn(
            "src/main/java/com/example/DemoApplication.java",
            self.candidate_paths(payload, "cache"),
        )
        self.assertTrue(
            all(
                "No Redis configuration signal detected" not in risk
                for risk in payload["risks"]
            )
        )

    def test_skip_rules_ignore_uv_and_tmp_noise(self) -> None:
        repo_root = self.make_repo(
            {
                "src/app.ts": (
                    'import session from "express-session";\n'
                    "app.use(session({ secret: 'demo' }));\n"
                ),
                ".uv-cache/noisy.py": "cache = Redis.from_url('redis://localhost')\n",
                ".uv-python/noisy.py": "limiter = Limiter(key_func=lambda request: request.client.host)\n",
                "_tmp_fixture/noisy.py": "from celery import Celery\n",
            }
        )

        payload = self.run_cli(repo_root)

        all_paths = {
            item["path"]
            for bucket in payload["integration_candidates"].values()
            for item in bucket
        }
        self.assertIn("src/app.ts", all_paths)
        self.assertNotIn(".uv-cache/noisy.py", all_paths)
        self.assertNotIn(".uv-python/noisy.py", all_paths)
        self.assertNotIn("_tmp_fixture/noisy.py", all_paths)


if __name__ == "__main__":
    unittest.main()
