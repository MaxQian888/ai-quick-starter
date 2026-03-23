# Content And Navigation

Use this file when the job is about writing documents, organizing the docs tree, or fixing how navigation is generated.

## Page Tree Model

Official pages:

- https://www.fumadocs.dev/docs/page-conventions
- https://www.fumadocs.dev/docs/headless/source-api
- https://www.fumadocs.dev/docs/markdown

## Frontmatter

Fumadocs uses frontmatter to build page metadata and page-tree labels.

The common page-level properties are:

- `title`
- `description`
- `icon`

On Fumadocs UI, frontmatter `title` is typically the page h1, so a Markdown `# Heading` is often unnecessary unless the repo uses custom title rendering.

## Slugs

- Slugs default to file paths relative to the docs content directory.
- `dir/page.mdx` becomes `['dir', 'page']`.
- `dir/index.mdx` becomes `['dir']`.

Use custom slug generation only when the repo truly needs it; otherwise keep file-path conventions.

## Folder Conventions

### Folder Group

Wrap a folder name in parentheses to keep the folder out of generated slugs:

- `./(group-name)/page.mdx` becomes `['page']`

Use this to group content physically without changing URLs.

### Root Folder

Mark a folder as a root tab by adding `root: true` in `meta.json`:

```json
{
  "title": "Name of Folder",
  "description": "Optional",
  "root": true
}
```

In Fumadocs UI, root folders surface as layout tabs.

## `meta.json`

Use `meta.json` to control folder-level behavior:

- `title`
- `icon`
- `defaultOpen`
- `collapsible`
- `pages`

Use `pages` when default alphabetical ordering is not enough. When `pages` is specified, only listed items are included.

Useful `pages` patterns from the docs:

- relative path entry
- separator
- external or internal links
- `...` rest
- `z...a` reversed rest
- `...folder` extract
- `!item` exclusion

Never allow the same page URL to appear more than once in the page tree.

## Loader Responsibilities

`loader()` is the unified server-side source layer. Use it for:

- `source.getPage(...)`
- `source.getPages(...)`
- `source.getPageTree(...)`
- `source.generateParams()`
- `source.getLanguages()`

It can also customize:

- `baseUrl` or dynamic URL generation
- slug generation
- icon resolution
- i18n routing

## MDX Authoring Features

The official Markdown guide highlights these built-ins:

- Cards and `Card`
- Callouts
- heading anchors
- TOC controls with `[!toc]` and `[toc]`
- custom anchors with `[#my-heading-id]`
- code blocks with titles and line numbers
- Shiki transformers
- tab groups
- `<include>` for Fumadocs MDX
- npm command blocks

Prefer these supported authoring features before inventing repo-local markdown conventions.

## Relative Links

Fumadocs exposes `createRelativeLink()` for MDX links that reference nearby files:

- use it when docs authors write `./file.mdx` style links
- wire it from the current page plus `source`

This is a targeted seam for repo migrations from pure Markdown trees.
