from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SKILL_ROOT / 'scripts' / 'print_fumadocs_reference_map.py'
SPEC = importlib.util.spec_from_file_location('print_fumadocs_reference_map', SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FumadocsReferenceMapTests(unittest.TestCase):
    def test_required_skill_files_exist(self) -> None:
        required_paths = [
            SKILL_ROOT / 'SKILL.md',
            SKILL_ROOT / 'references' / 'official-doc-map.md',
            SKILL_ROOT / 'references' / 'setup-and-architecture.md',
            SKILL_ROOT / 'references' / 'content-and-navigation.md',
            SKILL_ROOT / 'references' / 'ui-search-i18n-and-deploy.md',
            SKILL_ROOT / 'scripts' / 'print_fumadocs_reference_map.py',
            SKILL_ROOT / 'agents' / 'openai.yaml',
        ]

        for path in required_paths:
            self.assertTrue(path.exists(), msg=f'missing required skill file: {path}')

    def test_scenarios_cover_complete_skill_surface(self) -> None:
        expected = {
            'scaffold',
            'manual-next',
            'content',
            'ui',
            'search',
            'i18n',
            'static',
            'customize',
        }
        self.assertEqual(set(MODULE.SCENARIO_MAP), expected)

    def test_all_urls_point_to_official_fumadocs_docs(self) -> None:
        for items in MODULE.SCENARIO_MAP.values():
            for item in items:
                self.assertTrue(
                    item['official_url'].startswith('https://www.fumadocs.dev/docs'),
                    msg=f"unexpected official url: {item['official_url']}",
                )

    def test_cli_json_output_for_ui_scenario(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), '--scenario', 'ui', '--json'],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

        payload = json.loads(result.stdout)
        self.assertEqual(payload['scenario'], 'ui')
        topics = [item['topic'] for item in payload['references']]
        self.assertIn('docs-layout', topics)
        self.assertIn('docs-page', topics)
        self.assertIn('theme', topics)

    def test_skill_description_mentions_complete_fumadocs_work(self) -> None:
        content = (SKILL_ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('manual installation', content)
        self.assertIn('internationalization', content)
        self.assertIn('static export', content)


if __name__ == '__main__':
    unittest.main()
