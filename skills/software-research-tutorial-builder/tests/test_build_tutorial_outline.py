import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_tutorial_outline.py"


class BuildTutorialOutlineTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("build_tutorial_outline", SCRIPT_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_outline_contains_required_sections(self):
        module = self.load_module()
        brief = {
            "software": "Acme CLI",
            "versions": ["1.2.0"],
            "platforms": ["windows"],
            "prerequisites": ["Python 3.11"],
            "core_concepts": ["profiles", "workspaces"],
            "command_inventory": ["uv tool install acme-cli"],
            "verified_claims": ["Install with uv tool install acme-cli."],
            "unresolved_questions": [],
            "topic_notes": {"usage": ["Profiles are stored locally."]},
        }

        outline = module.build_outline(brief)

        self.assertIn("# Acme CLI Tutorial Outline", outline)
        self.assertIn("## 1. What This Software Is For", outline)
        self.assertIn("## 5. First Runnable Example", outline)
        self.assertIn("## 7. Common Mistakes And Troubleshooting", outline)

    def test_outline_includes_support_material_checklist_and_case_placeholders(self):
        module = self.load_module()
        brief = {
            "software": "Acme CLI",
            "versions": ["1.2.0"],
            "platforms": ["windows"],
            "prerequisites": ["Python 3.11"],
            "core_concepts": ["profiles"],
            "command_inventory": ["uv tool install acme-cli"],
            "verified_claims": ["Install with uv tool install acme-cli."],
            "unresolved_questions": ["Confirm Linux path behavior."],
            "topic_notes": {"troubleshooting": ["PATH is commonly misconfigured."]},
        }

        outline = module.build_outline(brief)

        self.assertIn("## Support-Material Checklist", outline)
        self.assertIn("- [ ] Environment variable example", outline)
        self.assertIn("Minimal runnable case", outline)
        self.assertIn("Troubleshooting case", outline)

    def test_outline_surfaces_conflicts_and_unverified_topics(self):
        module = self.load_module()
        brief = {
            "software": "Acme CLI",
            "versions": ["1.2.0"],
            "platforms": ["windows"],
            "prerequisites": ["Python 3.11"],
            "core_concepts": ["profiles"],
            "command_inventory": ["uv tool install acme-cli"],
            "verified_claims": ["Install with uv tool install acme-cli."],
            "unresolved_questions": [],
            "topic_notes": {},
            "conflicts": {
                "installation": [
                    {"track": "official", "claim": "Install with uv tool install acme-cli."},
                    {"track": "community", "claim": "Install with pipx install acme-cli."},
                ]
            },
            "unverified_topics": ["installation"],
        }

        outline = module.build_outline(brief)

        self.assertIn("## Conflicts To Resolve", outline)
        self.assertIn("installation", outline)
        self.assertIn("## Unverified Topics", outline)


if __name__ == "__main__":
    unittest.main()
