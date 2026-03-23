# Module Selection

## Pick Modules That Improve Navigation

Choose module docs for directories that are high-value orientation points, such as:
- the main documentation hub,
- the best representative skill examples,
- the newest or actively maintained feature area,
- or the strongest implementation seam in the repository.

## Good Module Candidates

- directories with both a `SKILL.md` and supporting `agents/`, `references/`, `scripts/`, or `tests/`,
- directories that explain repository conventions by example,
- documentation folders that collect designs, plans, or standards,
- imported template corpora only when they materially affect contributor navigation.

## Usually Skip

- `node_modules`,
- `dist`,
- cache directories,
- temp fixtures,
- binary-only asset trees,
- throwaway validation output,
- directories that merely duplicate an external source of truth.

## Module Count Heuristic

Default to 3-8 module docs.

If the repository is broad:
- start with the root doc,
- pick the top 3-5 highest-signal modules,
- list the rest as future scan candidates instead of generating shallow docs for everything.

## In Skill Collections

For a repository that contains many top-level skills:
- write module docs for the best pattern examples,
- use the root doc to describe the rest as sibling skills,
- and avoid cloning the same explanation into every skill folder.
