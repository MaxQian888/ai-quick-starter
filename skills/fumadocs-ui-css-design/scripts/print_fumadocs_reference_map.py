from __future__ import annotations

import argparse
import json
import sys


SCENARIO_MAP = {
    "scaffold": [
        {
            "topic": "quick-start",
            "local_reference": "references/setup-and-architecture.md",
            "official_url": "https://www.fumadocs.dev/docs",
        },
        {
            "topic": "create-fumadocs-app",
            "local_reference": "references/setup-and-architecture.md",
            "official_url": "https://www.fumadocs.dev/docs/cli/create-fumadocs-app",
        },
    ],
    "manual-next": [
        {
            "topic": "manual-next-installation",
            "local_reference": "references/setup-and-architecture.md",
            "official_url": "https://www.fumadocs.dev/docs/manual-installation/next",
        },
        {
            "topic": "root-provider",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/layouts/root-provider",
        },
        {
            "topic": "theme",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/theme",
        },
    ],
    "content": [
        {
            "topic": "page-conventions",
            "local_reference": "references/content-and-navigation.md",
            "official_url": "https://www.fumadocs.dev/docs/page-conventions",
        },
        {
            "topic": "markdown",
            "local_reference": "references/content-and-navigation.md",
            "official_url": "https://www.fumadocs.dev/docs/markdown",
        },
        {
            "topic": "loader-api",
            "local_reference": "references/content-and-navigation.md",
            "official_url": "https://www.fumadocs.dev/docs/headless/source-api",
        },
    ],
    "ui": [
        {
            "topic": "root-provider",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/layouts/root-provider",
        },
        {
            "topic": "docs-layout",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/layouts/docs",
        },
        {
            "topic": "docs-page",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/layouts/page",
        },
        {
            "topic": "theme",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/theme",
        },
        {
            "topic": "components",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/components",
        },
    ],
    "search": [
        {
            "topic": "orama-search",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/headless/search/orama",
        },
        {
            "topic": "search-ui",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/search",
        },
    ],
    "i18n": [
        {
            "topic": "next-i18n",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/internationalization/next",
        },
        {
            "topic": "i18n-config",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/headless/internationalization/config",
        },
        {
            "topic": "loader-api",
            "local_reference": "references/content-and-navigation.md",
            "official_url": "https://www.fumadocs.dev/docs/headless/source-api",
        },
    ],
    "static": [
        {
            "topic": "static-build",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/deploying/static",
        },
        {
            "topic": "orama-search",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/headless/search/orama",
        },
    ],
    "customize": [
        {
            "topic": "docs-layout",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/layouts/docs",
        },
        {
            "topic": "docs-page",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/layouts/page",
        },
        {
            "topic": "search-ui",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/search",
        },
        {
            "topic": "components",
            "local_reference": "references/ui-search-i18n-and-deploy.md",
            "official_url": "https://www.fumadocs.dev/docs/ui/components",
        },
    ],
}


def build_payload(scenario: str) -> dict[str, object]:
    if scenario == "all":
        return {
            "scenario": "all",
            "available_scenarios": sorted(SCENARIO_MAP),
            "references": SCENARIO_MAP,
        }

    return {
        "scenario": scenario,
        "available_scenarios": sorted(SCENARIO_MAP),
        "references": SCENARIO_MAP[scenario],
    }


def render_text(payload: dict[str, object]) -> str:
    lines = [
        f"scenario: {payload['scenario']}",
        "available_scenarios: " + ", ".join(payload["available_scenarios"]),
    ]

    references = payload["references"]
    if isinstance(references, dict):
        for name, items in references.items():
            lines.append(f"[{name}]")
            for item in items:
                lines.append(
                    f"- {item['topic']} | {item['local_reference']} | {item['official_url']}"
                )
    else:
        for item in references:
            lines.append(
                f"- {item['topic']} | {item['local_reference']} | {item['official_url']}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print curated local-reference and official-doc routes for common Fumadocs scenarios.",
    )
    parser.add_argument(
        "--scenario",
        default="all",
        choices=["all", *sorted(SCENARIO_MAP)],
        help="Scenario to print. Defaults to all.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of plain text.",
    )
    args = parser.parse_args()

    payload = build_payload(args.scenario)
    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_text(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
