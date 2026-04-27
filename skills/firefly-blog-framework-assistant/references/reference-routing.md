# Firefly Reference Routing

Use this file as a quick index before loading detailed snapshots.

## Config Files To Documentation

- `src/config/siteConfig.ts` -> `pages/en/guide/site.md`
- `src/config/navBarConfig.ts` -> `pages/en/guide/navbar.md`
- `src/config/sidebarConfig.ts` -> `pages/en/guide/sidebar.md`
- `src/config/profileConfig.ts` -> `pages/en/guide/profile.md`
- `src/config/backgroundWallpaper.ts` -> `pages/en/guide/wallpaper.md`
- `src/config/commentConfig.ts` -> `pages/en/guide/comment.md`
- `src/config/musicConfig.ts` -> `pages/en/guide/music.md`
- `src/config/fontConfig.ts` -> `pages/en/guide/font.md`
- `src/config/coverImageConfig.ts` -> `pages/en/guide/cover-image.md`
- `src/config/expressiveCodeConfig.ts` -> `pages/en/guide/code-block.md`
- `src/config/sakuraConfig.ts` -> `pages/en/guide/sakura.md`
- `src/config/announcementConfig.ts` -> `pages/en/guide/announcement.md`
- `src/config/footerConfig.ts` -> `pages/en/guide/footer.md`
- `src/config/licenseConfig.ts` -> `pages/en/guide/license.md`
- `src/config/friendsConfig.ts` -> `pages/en/guide/friends.md`
- `src/config/sponsorConfig.ts` -> `pages/en/guide/sponsor.md`
- `src/config/adConfig.ts` -> `pages/en/guide/ad.md`
- `src/config/pioConfig.ts` -> `pages/en/guide/pio.md`

## Workflow Topics

- Initial setup and local run:
  - `pages/en/guide/getting-started.md`
- Writing and content markdown features:
  - `pages/en/guide/writing.md`
  - `pages/en/guide/password.md`
  - `pages/en/guide/gallery.md`
- Deployment and release:
  - `pages/en/guide/deploy.md`
  - `pages/en/guide/update.md`
- Policy and attribution:
  - `pages/en/guide/license.md`

## Locale Mirror

- English pages live under `pages/en/...`.
- Chinese pages live under `pages/zh/...`.
- For bilingual output, pair each `pages/en/guide/*.md` file with `pages/zh/guide/*.md` of the same slug.

## Evidence Policy

- Reference `index.json` for canonical URL and crawl timestamp.
- Quote exact option names and enum values from page snapshots.
- If a key is not found by `rg`, treat it as unsupported until verified.
