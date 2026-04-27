---
name: firefly-blog-framework-assistant
description: |
  Use this skill whenever the user is building, configuring, customizing, deploying, upgrading, or troubleshooting a Firefly blog project.
  Make sure to use this skill whenever the request mentions Firefly, Astro blog, src/config/*.ts, theme modules, navbar/sidebar/profile config,
  deployment to Vercel/Netlify/Cloudflare, content writing rules, gallery, comments, or wallpaper settings.
  Also trigger for synonyms like "my blog uses Firefly", "CuteLeaf docs", or when the user asks about Firefly-specific options,
  post behaviors, cover images, code blocks, or monetization features. Refresh references from docs-firefly.cuteleaf.cn when docs may be stale.
---

# Firefly Blog Framework Assistant

Use Firefly documentation as the primary source of truth, then convert requirements into concrete file-level actions for the target repository.

## Adaptive Detection

Before proposing changes, detect the project shape:

1. **Framework**: confirm the repo is an Astro-based Firefly project (look for `astro.config.*`, `src/config/*.ts`).
2. **Language preference**: check if the user writes content in Chinese or English to route docs to `zh/` or `en/` paths.
3. **Config surface**: inspect `src/config/` for `site.ts`, `navBar.ts`, `sidebar.ts`, `profile.ts` to understand what is already customized.
4. **Deployment target**: look for `vercel.json`, `netlify.toml`, or Cloudflare Pages signals.
5. **Theme features**: scan for existing wallpaper, font, music, or comment integrations before adding duplicates.

## Workflow

1. Confirm the user goal and map it to Firefly areas (config, content, UI feature, deploy, update).
2. Read `references/firefly-docs/index.json` first to locate relevant pages quickly.
3. Read only the required page snapshots from `references/firefly-docs/pages/`.
4. If extracted text looks incomplete for a page, open the paired raw snapshot in `references/firefly-docs/raw/`.
5. Produce repository actions with exact file paths and minimal, reversible edits.
6. If docs may be outdated, refresh references before final guidance.

## Examples

**Customize the navbar:**
```bash
# Read the navbar config reference first, then edit src/config/navBar.ts
```

**Deploy to Vercel:**
```bash
# Read references/firefly-docs/pages/en/guide/deploy.md
# Follow the official deployment steps and verify build output
```

## Topic Routing

Use this map to narrow reference loading before proposing changes.

- Project bootstrap and architecture:
  - `references/firefly-docs/pages/en/guide/getting-started.md`
  - `references/firefly-docs/pages/en/guide/site.md`
- Content authoring and post behaviors:
  - `references/firefly-docs/pages/en/guide/writing.md`
  - `references/firefly-docs/pages/en/guide/password.md`
  - `references/firefly-docs/pages/en/guide/gallery.md`
- Navigation and profile surfaces:
  - `references/firefly-docs/pages/en/guide/navbar.md`
  - `references/firefly-docs/pages/en/guide/sidebar.md`
  - `references/firefly-docs/pages/en/guide/profile.md`
  - `references/firefly-docs/pages/en/guide/footer.md`
- Theme and media features:
  - `references/firefly-docs/pages/en/guide/wallpaper.md`
  - `references/firefly-docs/pages/en/guide/font.md`
  - `references/firefly-docs/pages/en/guide/cover-image.md`
  - `references/firefly-docs/pages/en/guide/code-block.md`
  - `references/firefly-docs/pages/en/guide/sakura.md`
  - `references/firefly-docs/pages/en/guide/music.md`
  - `references/firefly-docs/pages/en/guide/pio.md`
- Community and monetization:
  - `references/firefly-docs/pages/en/guide/comment.md`
  - `references/firefly-docs/pages/en/guide/announcement.md`
  - `references/firefly-docs/pages/en/guide/friends.md`
  - `references/firefly-docs/pages/en/guide/sponsor.md`
  - `references/firefly-docs/pages/en/guide/ad.md`
- Deployment and lifecycle:
  - `references/firefly-docs/pages/en/guide/deploy.md`
  - `references/firefly-docs/pages/en/guide/update.md`
  - `references/firefly-docs/pages/en/guide/license.md`

For Chinese-first requests, prefer mirrored paths under `references/firefly-docs/pages/zh/guide/`.

## Fast Lookup Patterns

Use ripgrep against crawled snapshots to avoid broad reads.

```bash
rg -n "siteConfig|navBarConfig|sidebarConfig|profileConfig" references/firefly-docs/pages
rg -n "deploy|Vercel|Netlify|Cloudflare|GitHub" references/firefly-docs/pages/en/guide/deploy.md
rg -n "comment|giscus|twikoo|waline|artalk" references/firefly-docs/pages
rg -n "music|meting|playlist|local" references/firefly-docs/pages
```

## Refresh References

Re-crawl the full Firefly docs site (both `en` and `zh`) whenever docs may have changed.

```bash
python scripts/crawl_firefly_docs.py \
  --start-url https://docs-firefly.cuteleaf.cn/ \
  --path-prefix / \
  --output-dir references/firefly-docs \
  --json
```

Expected artifacts after refresh:

- `references/firefly-docs/index.json`
- `references/firefly-docs/catalog.md`
- `references/firefly-docs/pages/**/*.md`
- `references/firefly-docs/raw/**/*.html`

## Guardrails

- Do not invent config keys or workflow steps that are absent from Firefly docs snapshots.
- Prefer exact option names and value shapes from docs before proposing edits.
- Separate Firefly-native guidance from generic Astro guidance; do not merge them silently.
- If docs and user code diverge, state the divergence and propose a minimal migration path.
- Keep references current by rerunning crawler before high-stakes migration or deployment advice.
