# Strategy Selection

## Goal

Map repository shape to the safest i18n rollout strategy.

## Recommended Default Choices

- `next-intl`
  - Prefer when the repository is primarily Next.js and no other i18n stack is already dominant.
  - Best fit for App Router or Pages Router projects that need route-aware locale loading.
- `react-i18next`
  - Prefer when the repository is a React SPA or mixed React client surface without Next.js locale wiring.
  - Good fit when the app already uses client-side state and route-based rendering.
- `vue-i18n`
  - Prefer when the repository is primarily Vue.
- `gettext`
  - Prefer when the repository is Python-only or when translations are already managed through gettext catalogs.

## Strategy Modes

- `extend-existing`
  - Use when one stack is already present with medium or high confidence.
  - Reuse the current bootstrap, provider, and message layout.
- `introduce-new`
  - Use when no stack exists and the repository profile clearly points to one framework.
  - Add bootstrap first, then one representative localized flow, then widen.
- `blocked`
  - Use when multiple frameworks, multiple apps, or unclear ownership make a single recommendation unsafe.

## Rollout Sequence

1. Confirm app scope and runtime entrypoints.
2. Add or reuse the bootstrap layer.
3. Add one locale and one namespace or message file.
4. Localize one representative route, page, or component cluster.
5. Verify runtime behavior, locale switching, fallback behavior, and message loading.
6. Expand only after the first slice is stable.

## Escalation Rules

- Escalate when the repository mixes server-rendered and client-rendered apps with different needs.
- Escalate when package dependencies and code imports point to different stacks.
- Escalate when a custom localization wrapper hides the real provider and message layout.
