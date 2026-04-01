# Generated Skill Contract

## Required Files

Every generated package should contain:

- `SKILL.md`
- `CLAUDE.md`
- `agents/openai.yaml`
- `references/project-map.md`
- `references/working-rules.md`
- `artifacts/project-analysis.json`

## File Responsibilities

### `SKILL.md`

State what the generated skill is for, when to invoke it, how to start reading the repository, and what guardrails to preserve.

### `CLAUDE.md`

Provide a fast module map for the generated package itself: purpose, read order, output contract, and the boundary between observed scan facts and generated guidance.

### `agents/openai.yaml`

Expose a stable display name, short UI description, and a default prompt that explicitly mentions the generated skill name.

### `references/project-map.md`

Capture the observed repository snapshot:

- source root,
- docs,
- manifests,
- language mix,
- important directories,
- command hints,
- likely entrypoints,
- and suggested reading order.

### `references/working-rules.md`

Capture how to use the generated skill responsibly:

- trigger patterns,
- observed facts versus heuristics,
- skip areas,
- scan limits,
- and refresh guidance.

### `artifacts/project-analysis.json`

Preserve the machine-readable scan so later edits can see the original generation evidence.

## Quality Bar

- Observed files and manifests should be accurate.
- Commands should come from repository signals when possible.
- Heuristic sections should be labeled honestly.
- The generated skill should reduce future onboarding cost without pretending to know runtime truth it did not verify.
- Re-generation should require an explicit overwrite signal rather than silently replacing an existing package.
