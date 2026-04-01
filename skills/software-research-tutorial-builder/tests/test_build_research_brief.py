import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_research_brief.py"


class BuildResearchBriefTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("build_research_brief", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_merge_findings_combines_sources_and_commands(self):
        module = self.load_module()
        findings = [
            {
                "software": "Acme CLI",
                "track": "official",
                "topic": "installation",
                "claim": "Install with uv tool install acme-cli.",
                "source": "Official docs",
                "url": "https://example.com/docs/install",
                "version": "1.2.0",
                "platforms": ["windows"],
                "prerequisites": ["Python 3.11"],
                "commands": ["uv tool install acme-cli"],
                "verified": True,
            },
            {
                "software": "Acme CLI",
                "track": "community",
                "topic": "usage",
                "claim": "Set ACME_HOME before the first run on Windows.",
                "source": "Community blog",
                "url": "https://example.com/blog/acme-cli-windows",
                "version": "1.2.0",
                "platforms": ["windows"],
                "commands": ["$env:ACME_HOME=\"$HOME\\.acme\""],
                "questions": ["Confirm whether ACME_HOME is still needed on macOS."],
            },
        ]

        brief = module.merge_findings(findings)

        self.assertEqual(brief["software"], "Acme CLI")
        self.assertEqual(brief["versions"], ["1.2.0"])
        self.assertEqual(len(brief["source_inventory"]), 2)
        self.assertIn("Python 3.11", brief["prerequisites"])
        self.assertIn("uv tool install acme-cli", brief["command_inventory"])
        self.assertEqual(brief["verified_claims"], ["Install with uv tool install acme-cli."])
        self.assertIn("Confirm whether ACME_HOME is still needed on macOS.", brief["unresolved_questions"])

    def test_render_markdown_includes_verification_and_unresolved_sections(self):
        module = self.load_module()
        brief = {
            "software": "Acme CLI",
            "versions": ["1.2.0"],
            "platforms": ["windows"],
            "prerequisites": ["Python 3.11"],
            "core_concepts": ["profiles"],
            "command_inventory": ["uv tool install acme-cli"],
            "source_inventory": [{"track": "official", "source": "Official docs", "url": "https://example.com"}],
            "verified_claims": ["Install with uv tool install acme-cli."],
            "unresolved_questions": ["Check Linux path behavior."],
            "topic_notes": {"usage": ["Profiles are stored locally."]},
        }

        markdown = module.render_markdown(brief)

        self.assertIn("# Acme CLI Research Brief", markdown)
        self.assertIn("## Verified Claims", markdown)
        self.assertIn("Install with uv tool install acme-cli.", markdown)
        self.assertIn("## Unresolved Questions", markdown)
        self.assertIn("Check Linux path behavior.", markdown)


if __name__ == "__main__":
    unittest.main()
