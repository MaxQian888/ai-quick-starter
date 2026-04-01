# Detection Playbook

## Goal

Identify the repository shape and any existing i18n stack before recommending project-level localization support.

## Signal Order

1. Runtime and package manifests
2. Existing framework entrypoints and route layout
3. Existing i18n imports, hooks, providers, locale trees, and message files
4. Existing translation key naming or namespace conventions
5. Only after the above: representative user-facing surfaces that still contain raw strings

## Project Profile Signals

- Next.js:
  - `next` in `package.json`
  - `app/` or `pages/`
- React SPA:
  - `react` with `vite`, `react-router`, or SPA entry files
- Vue:
  - `vue`, `vue-router`, or `.vue` surfaces
- Python:
  - `pyproject.toml`, `requirements*.txt`, or `.py` app entrypoints

## Stop Conditions

Stop automatic framework selection when any of these is true:

- Two i18n frameworks score similarly and neither is dominant
- The repository contains multiple first-class app surfaces that likely need different i18n strategies
- A custom translation wrapper exists but its bootstrap path is still unclear
- The repository is a monorepo and the target app has not been identified yet

## Safe Rollout Bias

Prefer:

- Reusing the existing provider, hook, namespace, and message file layout
- Choosing one app surface and one representative flow first
- Verifying the bootstrap before localizing many components

Avoid:

- Adding a second provider or parallel locale tree
- Choosing a framework only from ecosystem popularity
- Converting the whole repository from one scan result
