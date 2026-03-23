---
name: fumadocs-ui-css-design
description: Use when building, extending, migrating, or customizing a Fumadocs documentation site, especially when Codex needs current official Fumadocs guidance for scaffolding, Next.js manual installation, content source setup, page tree and navigation, MDX authoring, layouts, search, internationalization, static export, or theme and CSS customization.
---

# Fumadocs Complete Workflow

Treat this skill as the complete Fumadocs guide for real implementation work. The folder name is legacy; the scope is no longer limited to UI and CSS.

## Start Here

1. Classify the task before touching code:
   - `scaffold`: create a new Fumadocs app
   - `manual-next`: integrate Fumadocs into an existing Next.js app
   - `content`: structure docs, slugs, meta files, MDX authoring
   - `ui`: layout, theme, CSS variables, components, page chrome
   - `search`: built-in Orama search or custom search UI
   - `i18n`: locale routing, middleware, provider wiring
   - `static`: static export and static search
   - `customize`: slot replacement or CLI-driven local customization
2. If the task is version-sensitive or asks for the latest behavior, browse official Fumadocs docs first. Start with [references/official-doc-map.md](references/official-doc-map.md).
3. Use the local helper when you want a quick routing table from scenario to docs:

```bash
python scripts/print_fumadocs_reference_map.py --scenario ui
python scripts/print_fumadocs_reference_map.py --scenario manual-next --json
```

4. Read only the relevant reference file:
   - [references/setup-and-architecture.md](references/setup-and-architecture.md)
   - [references/content-and-navigation.md](references/content-and-navigation.md)
   - [references/ui-search-i18n-and-deploy.md](references/ui-search-i18n-and-deploy.md)

## Workflow

### 1. Prefer The Right Entry Path

- For a brand new docs app, prefer the official scaffold path from Quick Start or `create-fumadocs-app`.
- For an existing app, prefer manual integration instead of forcing starter-project assumptions into the repo.
- For a partially integrated Fumadocs site, inspect `source.config.*`, `lib/source.*`, app routes, and global styles before suggesting changes.

### 2. Treat Content Source As The Foundation

- Establish the content source first, then layouts and cosmetics.
- On Next.js manual installs, keep the `source.config.ts` plus `fumadocs-mdx` plugin wiring accurate before touching page components.
- Use `loader()` as the truth source for page tree, URLs, `getPage`, `getPageTree`, and `generateStaticParams`.

### 3. Keep Navigation File-Driven When Possible

- Prefer `meta.json`, root folders, and file layout over hardcoded sidebar trees.
- Use explicit `pages` ordering only when the default alphabetical/file-driven output is not enough.
- Never allow duplicated URLs in the same page tree.

### 4. Use Fumadocs UI Through Supported Seams First

- Put `RootProvider` at the root layout.
- Use `DocsLayout` for sidebar/header/tabs structure.
- Use `DocsPage` for page shell concerns such as TOC, breadcrumb, footer, and page actions.
- Use theme CSS imports and CSS variables before reaching for global overrides.

### 5. Escalate Customization Through Official Mechanisms

- If supported props are enough, stay inside props and shared layout options.
- If you need deeper layout or slot control, prefer the official CLI:

```bash
npx @fumadocs/cli@latest customise
npx @fumadocs/cli@latest add slots/docs/page/toc
```

- Replace slots surgically instead of forking large layout files prematurely.

### 6. Keep Search, I18n, And Deployment Aligned

- Search choice affects deployment. Built-in search can run server-side or static; static search moves index cost to the browser.
- i18n affects routing, middleware, `RootProvider`, loader config, and page/layout param handling together. Do not patch only one layer.
- Static export requires framework config plus search configuration that matches static mode.

## Scenario Rules

### Scaffold

- Start from official scaffold docs, not custom boilerplate.
- Preserve the user's chosen framework and package manager.
- Do not promise starter defaults that the target template may no longer include; verify first.

### Manual Next.js Integration

- Confirm the app already uses Next.js and Tailwind in the versions required by current docs.
- Keep `next.config.mjs` ESM-friendly if using `fumadocs-mdx`.
- Check that the body gets the required layout class when wiring `RootProvider`.

### Content And Authoring

- Use frontmatter for page title/description/icon.
- Use page-tree conventions, `meta.json`, and root folders instead of ad hoc nav registries where possible.
- Use built-in MDX affordances such as Cards, Callouts, headings, tabs, include, and relative links before inventing custom markdown syntax.

### UI And Theme

- Import Fumadocs UI CSS presets instead of recreating the base design tokens.
- Prefer semantic CSS variables like `--fd-layout-width` and `--color-fd-*`.
- Avoid broad global overrides that fight the preset or built-in typography behavior.

### Search

- Use built-in Orama unless there is a concrete reason to move to another backend.
- For large static sites, reconsider built-in static search because clients must download the exported index.
- For multilingual Chinese or Japanese search, remember tokenizer setup requirements.

### Internationalization

- Define shared i18n config first.
- Move pages into the locale segment and pass locale to both loader and layouts.
- Keep locale-aware navigation outside Fumadocs layouts explicit; Fumadocs only manages its own layout navigation.

### Static Export

- Configure framework static output explicitly.
- Pair static deployment with static-capable search configuration.
- Re-check route generation and trailing-slash behavior instead of assuming defaults.

## Guardrails

- Prefer official Fumadocs docs over memory for anything version-sensitive.
- Do not guess path names for layout files, routes, or package APIs when the docs or repo can confirm them.
- Do not reduce Fumadocs work to "just style it"; content source, routing, search, and layout seams matter first.
- Do not over-customize layout internals before exhausting props, shared options, CSS variables, and CLI slot extraction.
- Do not recommend static export without addressing search behavior.
- Do not partially wire i18n; middleware, route structure, provider, and loader must agree.

## Output Shape

When answering or implementing Fumadocs work, prefer this order:

1. current task classification
2. confirmed official-doc path or repo seam
3. minimal implementation steps
4. targeted code or config changes
5. verification notes and caveats

## Reference Files

- Read [references/official-doc-map.md](references/official-doc-map.md) for the official URL map and current doc-entry choices.
- Read [references/setup-and-architecture.md](references/setup-and-architecture.md) for scaffold vs manual integration and the Next.js baseline.
- Read [references/content-and-navigation.md](references/content-and-navigation.md) for MDX authoring, slugs, `meta.json`, root folders, and relative-link behavior.
- Read [references/ui-search-i18n-and-deploy.md](references/ui-search-i18n-and-deploy.md) for Root Provider, layouts, themes, search, i18n, and static export.
