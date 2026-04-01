# Source Policy

Use this file when deciding whether a source belongs in the tutorial brief.

## Source Classes

### Official Sources

Examples:
- vendor docs,
- vendor GitHub repos,
- release notes,
- migration guides,
- official blog posts.

Use official sources for:
- installation methods,
- version support,
- API names,
- command syntax,
- and supported feature boundaries.

### Community Sources

Examples:
- trusted blog posts,
- maintainer issue replies,
- discussion threads,
- example repos,
- conference notes,
- and independent troubleshooting writeups.

Use community sources for:
- real setup friction,
- environment-specific failures,
- practical shortcuts,
- workflow examples,
- and migration gotchas.

## Ranking Rules

1. Prefer recent sources over stale sources when the software changes quickly.
2. Prefer primary evidence over derivative summaries.
3. Prefer sources that include concrete commands, versions, or reproducible examples.
4. Keep both official and community evidence when they solve different problems.

## Conflict Handling

If official and community guidance conflict:
- record the conflict,
- attach both sources,
- note the version and environment context,
- and do not flatten the disagreement into one claim without evidence.

## Verification Labels

Use these labels in the brief or final tutorial:
- `verified`: directly run or directly confirmed from authoritative product material.
- `source-backed`: supported by one or more sources but not executed locally.
- `uncertain`: conflicting or incomplete evidence.

## Freshness Rules

If the software is fast-moving, include a date or version note next to every important command or setup rule.

Do not reuse old community fixes without checking whether a newer official path supersedes them.
