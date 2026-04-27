# Backend Selection

Use these routes in order:

## General Web Pages

1. `Jina Reader`
2. `defuddle.md`
3. `markdown.new`
4. Raw HTML

## X / Twitter

1. FxTwitter API for single tweets
2. Nitter RSS for user timelines
3. Camofox snapshots for replies or article-style pages
4. Generic web fallback

## WeChat Articles

1. WeSpy when explicitly configured
2. `wechat-article-exporter` REST API when `--wechat-api` or `WECHAT_API_URL` is set
3. `Jina Reader`
4. `defuddle.md`
5. Raw HTML

## YouTube

1. Page-embedded structured data for single videos
2. Page-embedded browse data for channels and playlists
3. Generic web fallback

Supported surfaces:
- single video pages
- channel pages
- playlist pages

## Bilibili

1. Public video API for single videos
2. Optional page-embedded `__playinfo__` DASH extraction for explicit single-video media downloads
3. Public card API plus signed WBI video-list API for UP spaces
4. Public collection API for season or collection detail pages
5. Page-embedded state only as a fallback when API coverage is unavailable
6. Generic web fallback

Supported surfaces:
- single video pages
- UP homepages
- collection or list pages

Prefer the narrowest successful backend and fall back without mutating the local environment.
