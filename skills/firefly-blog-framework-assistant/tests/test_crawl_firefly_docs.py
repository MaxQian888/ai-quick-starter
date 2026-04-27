from __future__ import annotations

import unittest

from pathlib import Path
import sys


WORKSPACE_ROOT = Path(r"D:\Project\skills-test")
SCRIPT_DIR = WORKSPACE_ROOT / "firefly-blog-framework-assistant" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import crawl_firefly_docs as crawler  # noqa: E402


class CrawlFireflyDocsTests(unittest.TestCase):
    def test_normalize_href_strips_fragment_and_resolves_relative_path(self) -> None:
        base_url = "https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html"

        self.assertEqual(
            crawler.normalize_href(base_url, "../config/site-config.html#top"),
            "https://docs-firefly.cuteleaf.cn/en/config/site-config.html",
        )

    def test_is_doc_page_url_accepts_en_html_and_rejects_assets_or_external(self) -> None:
        self.assertTrue(
            crawler.is_doc_page_url(
                "https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html",
                "docs-firefly.cuteleaf.cn",
                "/en/",
            )
        )
        self.assertFalse(
            crawler.is_doc_page_url(
                "https://docs-firefly.cuteleaf.cn/assets/logo.svg",
                "docs-firefly.cuteleaf.cn",
                "/en/",
            )
        )
        self.assertFalse(
            crawler.is_doc_page_url(
                "https://example.com/en/guide/getting-started.html",
                "docs-firefly.cuteleaf.cn",
                "/en/",
            )
        )

    def test_url_to_relative_doc_path_maps_root_and_nested_pages(self) -> None:
        self.assertEqual(
            crawler.url_to_relative_doc_path("https://docs-firefly.cuteleaf.cn/en/"),
            "en/index",
        )
        self.assertEqual(
            crawler.url_to_relative_doc_path(
                "https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html"
            ),
            "en/guide/getting-started",
        )

    def test_extract_links_returns_normalized_unique_urls(self) -> None:
        html = """
        <html><body>
          <a href="/en/guide/getting-started.html">A</a>
          <a href="../config/site-config.html#x">B</a>
          <a href="https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html">C</a>
        </body></html>
        """
        base_url = "https://docs-firefly.cuteleaf.cn/en/guide/installation.html"
        links = crawler.extract_links(html, base_url)

        self.assertEqual(
            links,
            {
                "https://docs-firefly.cuteleaf.cn/en/guide/getting-started.html",
                "https://docs-firefly.cuteleaf.cn/en/config/site-config.html",
            },
        )

    def test_extract_main_text_prefers_main_tag_and_unescapes_entities(self) -> None:
        html = """
        <html><body>
          <header>Ignore me</header>
          <main>
            <h1>Firefly &amp; Docs</h1>
            <p>Hello <strong>World</strong></p>
          </main>
          <footer>Ignore too</footer>
        </body></html>
        """
        text = crawler.extract_main_text(html)

        self.assertIn("Firefly & Docs", text)
        self.assertIn("Hello World", text)
        self.assertNotIn("Ignore me", text)

    def test_extract_main_text_prefers_article_when_main_is_missing(self) -> None:
        html = """
        <html><body>
          <header>Ignore me</header>
          <article>
            <h1>Firefly Article</h1>
            <p>Only keep this section.</p>
          </article>
          <footer>Ignore too</footer>
        </body></html>
        """

        text = crawler.extract_main_text(html)

        self.assertIn("Firefly Article", text)
        self.assertIn("Only keep this section.", text)
        self.assertNotIn("Ignore me", text)
        self.assertNotIn("Ignore too", text)


if __name__ == "__main__":
    unittest.main()
