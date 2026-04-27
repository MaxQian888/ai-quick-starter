---
name: project-docs-sync
description: >
  Synchronize and update project documentation (README, CHANGELOG, docs/)
  to match the latest codebase implementation. Use this skill whenever the user
  wants to update documentation, keep docs in sync with code, refresh a README,
  write or update a CHANGELOG, or mentions that docs are outdated, stale, or
  inconsistent with the actual code. Also trigger when the user asks to document
  new features, describe recent changes, or improve project documentation
  accuracy — even if they don't explicitly say "sync" or "update docs".
---

# Project Docs Sync

Update project documentation to accurately reflect the latest codebase state.

Documentation rot is one of the most common sources of confusion in software
projects. This skill ensures that READMEs, CHANGELOGs, and other docs stay
aligned with the actual implementation by first researching the code thoroughly,
then updating the docs based on findings.

## When to Use

- The user wants to update, refresh, or rewrite project documentation
- The user mentions docs are "outdated", "stale", or "don't match the code"
- New features have been implemented but not documented
- A CHANGELOG needs to be updated after recent changes
- The README no longer accurately describes the project

## Core Workflow

Follow this workflow exactly. Do not skip the research phase — it is the
foundation of accurate documentation.

```
Phase 1: Survey      → Understand project structure and doc landscape
Phase 2: Research    → Spawn subagents to deeply study the implementation
Phase 3: Analyze     → Compare findings against existing docs
Phase 4: Update      → Write updated documentation
Phase 5: Validate    → Self-check for accuracy and completeness
```

### Phase 1: Survey the Project

Before spawning researchers, get a high-level view yourself:

1. **Identify the project type**: Read `package.json`, `Cargo.toml`,
   `pyproject.toml`, `go.mod`, `pom.xml`, or similar manifest files.
2. **List existing documentation**: Use `Glob` to find README files,
   CHANGELOG files, and files under common doc directories (`docs/`, `doc/`,
   `wiki/`, `.github/`).
3. **Read the current docs**: Read the README and CHANGELOG (if they exist)
   to understand what is already documented.
4. **Summarize the codebase**: Use `Glob` and `Grep` to understand the
   project structure — main source directories, entry points, key modules,
   and any recent changes (check `git log --oneline -20` if in a git repo).

From this survey, produce a brief summary:
- Project name and purpose
- Technology stack
- Existing documentation files and their state (accurate/stale/missing)
- Key areas where docs likely need updates

### Phase 2: Deep Research (Subagents)

This phase is critical. Spawn one or more research subagents to thoroughly
investigate the implementation. The goal is to extract facts about what the
code *actually* does — not what the docs claim it does.

**Spawn a research subagent** with this task (adapt based on project type):

```
You are a documentation researcher. Your job is to study this codebase
and produce a structured report of facts about the project's implementation.

Read the following areas thoroughly:
1. Entry points and public APIs (main files, lib exports, CLI commands)
2. Core features and functionality (read key source files)
3. Configuration options and environment variables
4. Dependencies and requirements
5. Build / test / development commands
6. Recent changes (last 10-20 commits if available)

For each area, note:
- What exists and how it works
- What has changed recently
- What is NOT yet documented (gaps)

Write your findings to <output-path>/research-report.md using this structure:

# Research Report: [Project Name]

## Entry Points & Public API
[List all entry points with brief descriptions]

## Core Features
[For each feature: name, description, key files involved]

## Configuration
[All config options, env vars, flags]

## Dependencies & Requirements
[Key runtime and dev dependencies with versions]

## Build / Test / Dev Commands
[Commands from package.json/scripts, Makefile, etc.]

## Recent Changes
[Summary of recent commits and their impact]

## Documentation Gaps
[Specific areas where docs are missing or inaccurate]
```

**Parallel research strategy**: For large projects, spawn multiple
subagents with focused scopes:
- One for "public API and features"
- One for "configuration and usage"
- One for "recent changes and CHANGELOG entries"

Each subagent should write its report to a separate file.

### Phase 3: Analyze Findings

Read all research reports. Compare findings against existing documentation:

1. **Feature coverage**: Does the README mention all major features?
2. **Accuracy**: Are the documented commands, options, and behaviors still
   correct?
3. **Freshness**: Do version numbers, requirements, and examples reflect
   the current state?
4. **Completeness**: Are there undocumented features, flags, or workflows?

Produce an analysis summary listing:
- Specific sections to update (file, section, what to change)
- New sections to add
- Outdated content to remove

### Phase 4: Update Documentation

Update docs based on your analysis. Follow these principles:

**For README updates:**
- Ensure the project description matches the actual purpose
- List all major features with accurate descriptions
- Update installation and usage instructions to match current code
- Verify all code examples work as described
- Update requirements/dependencies to match manifests
- Keep the README focused: overview, install, usage, features, contributing

**For CHANGELOG updates:**
- Read `references/changelog-formats.md` for format guidance
- Group changes by type: Added, Changed, Deprecated, Removed, Fixed, Security
- Reference specific versions and dates
- Include meaningful descriptions, not just commit messages
- Maintain chronological order (newest first)

**For other docs:**
- Update API references to match actual function signatures
- Update architecture docs to reflect current structure
- Ensure configuration docs list all available options

**Writing quality:**
- Use clear, concise language. Avoid jargon where possible; define it when
  necessary.
- Write in the same language as the existing docs (usually English or Chinese).
- Use active voice and present tense.
- Be specific: "Supports JSON and YAML input" is better than "Supports
  various formats".
- Ensure technical accuracy: every command, flag, and behavior you document
  must match the code.

### Phase 5: Validate

Before finishing, do a sanity check:

1. **Cross-check key claims**: Pick 3-5 important statements from your
   updated docs and verify them against the source code.
2. **Check consistency**: Ensure terminology is consistent across all docs.
3. **Verify examples**: If you included code examples, check they use
   correct syntax and API names.
4. **Review for hallucination**: Ensure you didn't add features or options
   that don't exist in the code.

If you find issues, fix them before presenting the final result.

## Output Format

Present the user with:

1. **A summary of changes**: What docs were updated and why
2. **The updated files**: Either inline (for small changes) or as file paths
3. **A list of research findings**: Key discoveries from the code that
   drove the documentation updates

If the user only wanted specific docs updated (e.g., "just update the
CHANGELOG"), respect that scope but still do the research phase — accuracy
requires understanding the code.

## Important Notes

- **Always research before writing.** Documentation written without reading
  the code is worse than outdated docs — it creates false confidence.
- **Preserve existing style.** Match the tone, formatting, and structure of
  the current documentation. Don't rewrite everything unless asked.
- **Be conservative with changes.** If something in the old docs is still
  accurate, keep it. Only change what needs changing.
- **Document what IS, not what SHOULD BE.** The docs describe the current
  implementation, not future plans or ideal behavior.
- **When in doubt, check the code.** If you are unsure about a feature's
  behavior, read the source rather than guessing.
