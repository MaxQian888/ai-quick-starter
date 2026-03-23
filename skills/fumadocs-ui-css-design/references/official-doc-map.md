# Official Doc Map

Checked against official Fumadocs docs on 2026-03-23.

Use this file first when the task asks for latest guidance, or when you need to decide which official page to open before editing code.

## Core Entry Points

| Scenario | Official Page | Why it matters |
| --- | --- | --- |
| quick overview | https://www.fumadocs.dev/docs | Current quick start, product split, and starter expectations |
| create new app | https://www.fumadocs.dev/docs/cli/create-fumadocs-app | Official app scaffold entrypoint and scriptable API |
| integrate into existing Next.js app | https://www.fumadocs.dev/docs/manual-installation/next | Current manual-install flow, package set, and required files |
| theme and CSS | https://www.fumadocs.dev/docs/ui/theme | Preset CSS imports, color variables, typography plugin notes |
| root provider | https://www.fumadocs.dev/docs/ui/layouts/root-provider | Search/theme provider seam and root placement |
| docs shell layout | https://www.fumadocs.dev/docs/ui/layouts/docs | Sidebar, tabs, banner, prefetch, and layout-system details |
| docs page shell | https://www.fumadocs.dev/docs/ui/layouts/page | TOC, footer, breadcrumb, last-updated, and slot replacement |
| MDX authoring | https://www.fumadocs.dev/docs/markdown | Frontmatter, callouts, cards, headings, tabs, include, code blocks |
| page tree conventions | https://www.fumadocs.dev/docs/page-conventions | Slugs, `meta.json`, root folders, page ordering, no-duplicate-url rule |
| source loader | https://www.fumadocs.dev/docs/headless/source-api | `loader()` responsibilities and output APIs |
| built-in search | https://www.fumadocs.dev/docs/headless/search/orama | Orama server, static mode, locale map, tokenizers |
| search UI | https://www.fumadocs.dev/docs/ui/search | Search dialog replacement and hotkey customization |
| Next.js i18n | https://www.fumadocs.dev/docs/internationalization/next | Locale routing, middleware, provider wiring, search caveats |
| shared i18n config | https://www.fumadocs.dev/docs/headless/internationalization/config | `defineI18n`, `hideLocale`, `fallbackLanguage` |
| static deployment | https://www.fumadocs.dev/docs/deploying/static | Static export and search mode implications |
| component catalog | https://www.fumadocs.dev/docs/ui/components | Built-in interactive docs components and MDX defaults |

## Current Official Facts Worth Remembering

- Quick Start currently states a minimum Node.js version of `22`.
- Manual Next.js installation currently assumes `Next.js 16` and `Tailwind CSS 4`.
- The official theme setup imports `fumadocs-ui/css/*.css` plus `fumadocs-ui/css/preset.css`.
- `RootProvider` includes `next-themes` support and search/theme configuration seams.
- Built-in search is based on Orama and supports static mode plus locale-specific configuration.

## Local Reference Pairing

| Need | Read local file next |
| --- | --- |
| scaffold or manual integration | [setup-and-architecture.md](setup-and-architecture.md) |
| writing docs and navigation | [content-and-navigation.md](content-and-navigation.md) |
| layouts, theme, search, i18n, deploy | [ui-search-i18n-and-deploy.md](ui-search-i18n-and-deploy.md) |
