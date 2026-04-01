from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
OPENAI_YAML = SKILL_ROOT / "agents" / "openai.yaml"
GUARDRAILS_REF = SKILL_ROOT / "references" / "postgres-guardrails.md"
RECIPES_REF = SKILL_ROOT / "references" / "query-recipes.md"
EXPLAIN_REF = SKILL_ROOT / "references" / "explain-and-index-review.md"
BUSINESS_REF = SKILL_ROOT / "references" / "business-query-patterns.md"


class PostgresSqlWriterPackageTests(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        for path in (SKILL_MD, OPENAI_YAML, GUARDRAILS_REF, RECIPES_REF, EXPLAIN_REF, BUSINESS_REF):
            self.assertTrue(path.exists(), msg=f"missing required file: {path}")

    def test_skill_frontmatter_and_body_capture_postgres_placeholder_contract(self) -> None:
        content = SKILL_MD.read_text(encoding="utf-8")

        self.assertNotIn("[TODO", content)
        self.assertNotIn("Structuring This Skill", content)
        self.assertRegex(
            content,
            r"^---\s+name:\s+postgres-sql-writer\s+description:\s+.+\s+---",
        )
        self.assertIn("PostgreSQL", content)
        self.assertIn("placeholder", content.lower())
        self.assertIn("Assumptions", content)
        self.assertIn("PostgreSQL SQL", content)
        self.assertIn("How To Adapt", content)
        self.assertIn("EXPLAIN", content)
        self.assertIn("index", content.lower())
        self.assertIn("grain", content.lower())
        self.assertIn("tenant", content.lower())

    def test_openai_metadata_mentions_skill_and_default_prompt(self) -> None:
        content = OPENAI_YAML.read_text(encoding="utf-8")

        self.assertIn('display_name: "PostgreSQL SQL Writer"', content)
        self.assertIn("short_description:", content)
        self.assertIn("default_prompt:", content)
        self.assertIn("$postgres-sql-writer", content)
        self.assertIn("EXPLAIN", content)
        self.assertIn("business", content.lower())

    def test_references_cover_guardrails_and_query_recipes(self) -> None:
        guardrails = GUARDRAILS_REF.read_text(encoding="utf-8")
        recipes = RECIPES_REF.read_text(encoding="utf-8")
        explain = EXPLAIN_REF.read_text(encoding="utf-8")
        business = BUSINESS_REF.read_text(encoding="utf-8")

        self.assertIn("WHERE", guardrails)
        self.assertIn("JOIN", guardrails)
        self.assertIn("parameter", guardrails.lower())
        self.assertIn("SELECT", recipes)
        self.assertIn("INSERT", recipes)
        self.assertIn("UPDATE", recipes)
        self.assertIn("JSONB", recipes)
        self.assertIn("ON CONFLICT", recipes)
        self.assertIn("EXPLAIN", explain)
        self.assertIn("EXPLAIN ANALYZE", explain)
        self.assertIn("Seq Scan", explain)
        self.assertIn("Index Scan", explain)
        self.assertIn("ORDER BY", explain)
        self.assertIn("tenant_id", business)
        self.assertIn("deleted_at", business)
        self.assertIn("audit", business.lower())
        self.assertIn("daily active users", business.lower())
        self.assertIn("orders", business.lower())


if __name__ == "__main__":
    unittest.main()
