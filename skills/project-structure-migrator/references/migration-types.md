# Migration Types

Use this file when the migration family is not obvious from the initial repository scan.

## `monorepo`

Use when the repository is moving toward an explicit workspace root.

Common signals:

- `pnpm-workspace.yaml`
- root `package.json` with `workspaces`
- `turbo.json` or `nx.json`
- clear `apps/` and `packages/` package roots

Default pressure:

- root scripts and installs need to coordinate multiple packages
- shared code should move into named packages instead of relative import sprawl

## `restructure`

Use when the repository is still one project, but its internal directory layout is hard to reason about.

Common signals:

- a single app root with mixed concerns under `src/`
- interleaved `components`, `pages`, `services`, `utils`, `api`, and `domain`
- fragile import paths or unclear entrypoint boundaries

Default pressure:

- improve boundaries without pretending the repo needs full workspace adoption

## `split-merge`

Use when multiple independent project surfaces must be split apart or merged together.

Common signals:

- several app-like roots without a unifying structure
- repeated manifests from previously separate projects
- duplicated tooling or runtime glue

Default pressure:

- stabilize ownership boundaries first
- keep compatibility shims longer than usual

## Decision Rules

- Prefer `monorepo` when workspace signals are explicit.
- Prefer `split-merge` when several app roots exist but no strong workspace contract exists yet.
- Prefer `restructure` when the repository still behaves like one project and the main problem is internal organization.
- If signals conflict, keep `auto` and surface the ambiguity in `open_questions`.
