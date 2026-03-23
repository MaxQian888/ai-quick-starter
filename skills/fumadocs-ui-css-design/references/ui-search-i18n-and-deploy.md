# UI, Search, I18n, And Deploy

Use this file when the task is about page chrome, theming, search, locale routing, or deployment behavior.

## UI Seams

Official pages:

- https://www.fumadocs.dev/docs/ui/theme
- https://www.fumadocs.dev/docs/ui/layouts/root-provider
- https://www.fumadocs.dev/docs/ui/layouts/docs
- https://www.fumadocs.dev/docs/ui/layouts/page
- https://www.fumadocs.dev/docs/ui/components
- https://www.fumadocs.dev/docs/ui/search

## Root Provider

`RootProvider` belongs in the root layout and owns shared Fumadocs UI context.

Important supported seams:

- `search={{ ... }}`
- `theme={{ ... }}`
- `i18n={provider(lang)}`
- `dir="rtl"`

The docs state that `RootProvider` includes `next-themes`.

## Theme And CSS

Current official baseline:

```css
@import 'tailwindcss';
@import 'fumadocs-ui/css/neutral.css';
@import 'fumadocs-ui/css/preset.css';
```

Alternatives:

- `fumadocs-ui/css/<theme>.css`
- `fumadocs-ui/css/shadcn.css`

Useful variables:

- `--fd-layout-width`
- `--color-fd-background`
- `--color-fd-foreground`
- `--color-fd-primary`
- `--color-fd-accent`

Prefer CSS variables and preset imports over large global overrides.

## Docs Layout

`DocsLayout` handles the sidebar and mobile header shell.

Supported customization seams include:

- `tree`
- `sidebar`
- `tabs`
- `sidebar.banner`
- `sidebar.components`
- `sidebar.prefetch`

For advanced changes the docs explicitly recommend:

```bash
npx @fumadocs/cli@latest customise
```

Use root folders in `meta.json` for layout tabs when possible instead of hardcoding the tabs array.

## Docs Page

`DocsPage` is the page shell for:

- TOC
- footer navigation
- breadcrumb
- page actions
- last updated time
- full-width mode

When supported props are insufficient, slot extraction is the official path:

```bash
npx @fumadocs/cli@latest add slots/docs/page/toc
npx @fumadocs/cli@latest add slots/docs/page/footer
npx @fumadocs/cli@latest add slots/docs/page/breadcrumb
npx @fumadocs/cli@latest add slots/docs/page/container
```

## Components

The UI components overview calls out:

- Accordion
- Banner
- Files
- Graph View
- Zoomable Image
- Inline TOC
- Steps
- Tabs
- Type Table

The default MDX component bundle also includes cards, callouts, code blocks, and headings.

## Search

Official pages:

- https://www.fumadocs.dev/docs/headless/search/orama
- https://www.fumadocs.dev/docs/ui/search

Built-in search defaults to Orama and is the recommended self-hosted option.

### Baseline Server

```ts
import { source } from '@/lib/source';
import { createFromSource } from 'fumadocs-core/search/server';

export const { GET } = createFromSource(source, {
  language: 'english',
});
```

### Key Search Rules

- Use `buildIndex()` when you need tags or other custom fields.
- For static sites, export `revalidate = false` and switch to `staticGET`.
- Static search downloads indexes into the client; this can be expensive for large docs sites.
- For large sites or managed search, prefer cloud solutions such as Algolia or Orama Cloud.

### Multilingual Search

- Use `localeMap` for locale-specific Orama settings.
- Chinese and Japanese need extra tokenizer configuration from `@orama/tokenizers`.
- Fumadocs UI handles locale-aware search UI if i18n is wired correctly.

## Search UI

Search UI can be configured from `RootProvider`.

Supported seams:

- disable search entirely
- replace the dialog component
- customize hotkeys
- provide custom markdown rendering for result content

Use the lower-level `SearchDialog` only when the default UI is insufficient.

## Internationalization

Official pages:

- https://www.fumadocs.dev/docs/internationalization/next
- https://www.fumadocs.dev/docs/headless/internationalization/config

Shared i18n starts with:

```ts
import { defineI18n } from 'fumadocs-core/i18n';

export const i18n = defineI18n({
  defaultLanguage: 'en',
  languages: ['en', 'cn'],
});
```

Next.js integration requires these layers to agree:

- middleware via `createI18nMiddleware(i18n)` or an equivalent custom middleware
- route structure such as `app/[lang]`
- `RootProvider i18n={provider(lang)}`
- `loader({ i18n, ... })`
- locale-aware `getPageTree(lang)` and layout options
- locale-aware search behavior

Useful config options:

- `hideLocale`
- `fallbackLanguage`

Remember that locale-aware links outside Fumadocs-owned layout navigation are still your responsibility.

## Static Export

Official page:

- https://www.fumadocs.dev/docs/deploying/static

For Next.js, the docs show:

```js
const nextConfig = {
  output: 'export',
};
```

Static export is only complete when search is also configured for static mode or replaced with a cloud solution.
