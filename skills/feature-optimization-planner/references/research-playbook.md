# Research Playbook

Use this file while running the audit. It maps the requested workflow onto the current tool surface and keeps the pass narrow, evidence-based, and reproducible.

## Tool Map

| Need | Prefer | Use it for |
|------|--------|------------|
| Semantic code discovery | augment context engine | Find likely files, seams, dependencies, and owning modules when the exact path is not obvious |
| Exact text or symbol search | `rg` in shell | Match exact identifiers, TODO markers, lint suppressions, suspicious APIs, or follow-up evidence after the semantic pass |
| Current framework or library docs | Context7 | Official or primary documentation for APIs, migrations, and best-practice guidance |
| Exact current page content | Fetch | Read a known docs URL, standard, or official article directly |
| Broader implementation research | Exa | Find current engineering writeups or representative examples after checking official docs |
| Open-source implementation study | DeepWiki | Inspect how a related public repository implements the same kind of feature |

## Phase 1: Initial Discovery

### 1. Lock the scope

- Record the repository root.
- Record the exact target folder.
- Record the optimization goal:
  - performance,
  - maintainability,
  - bug reduction,
  - UX consistency,
  - architecture cleanup,
  - test coverage,
  - security hardening.

If the user asks for a whole-repo backlog rather than a folder audit, switch to `$project-optimization-opportunity-auditor`.

### 2. Inventory the folder

- Enumerate subdirectories and files.
- Count source files, tests, config, and docs.
- Flag files that are unusually large or visibly overloaded.
- Note likely entrypoints, exports, routes, command handlers, or public APIs.

### 3. Read in dependency order

1. Entry route, page, command handler, public component, or main service.
2. State owner such as store, reducer, context, model, or controller.
3. Hooks, services, data loaders, repositories, or adapters.
4. Shared utilities, types, schemas, and constants.
5. Tests, mocks, and fixtures.
6. Local docs, specs, ADRs, or workflow notes that define intended behavior.

### 4. Build a quick dependency map

```markdown
## Dependency and Data-Flow Notes

- Entry:
- State or ownership:
- Services or hooks:
- Utilities:
- Types or schemas:
- Tests:
- External integrations:
- Cross-folder dependencies:
```

## Phase 2: Code Quality Analysis

Apply the detailed checklist from [issue-catalog.md](issue-catalog.md). Record only issues that are backed by local evidence.

### Evidence rules

- Prefer exact file paths and line references.
- Separate observed issues from inferred risks.
- If a claim depends on runtime behavior that was not exercised, label it as a risk or hypothesis, not a fact.
- If an issue seems intentional, say why it may be intentional and lower confidence instead of reporting it as a hard defect.

### Exact-search examples

Run exact-string searches only after the semantic pass narrows the surface.

```powershell
rg -n "TODO|FIXME|HACK|XXX" <target-path>
rg -n "console\\.(log|warn|error|debug)" <target-path>
rg -n "eslint-disable|ts-ignore|ts-expect-error" <target-path>
rg -n ": any\\b| as any\\b" <target-path>
rg -n "dangerouslySetInnerHTML|eval\\(|new Function\\(" <target-path>
rg -n "catch\\s*\\{\\s*\\}" <target-path>
```

Adapt patterns to the real stack. Do not force TypeScript checks onto Rust, Go, or Python code.

## Phase 3: Deep Analysis

Use semantic search and targeted reads to confirm:

- cross-file dependencies,
- data flow and state ownership,
- integration points and side effects,
- shared utility reuse,
- whether issues are local to the folder or symptoms of an upstream architectural seam.

If the root problem is mainly module boundaries or repository layering, route the deeper pass to `$project-architecture-design-analyzer`.

## Phase 4: External Research

### Preferred source order

1. Official framework or library docs.
2. Standards or vendor documentation.
3. High-quality engineering writeups with concrete examples.
4. Representative open-source repositories.

### What to capture from each source

- URL or repository name
- publication date or docs version when available
- the exact recommendation or pattern that matters
- whether the source is normative, advisory, or illustrative
- the mismatch between the source and the local implementation

### Good search shapes

- `"<framework> <feature> best practices"`
- `"<library> <feature> implementation example"`
- `"<feature> performance pitfalls"`
- `"<feature> architecture pattern"`

If the topic is library-specific, resolve the library in Context7 first and query the official docs before using broader search.

## Phase 5: Plan Construction

- Group the final plan by priority, not by file.
- Use the smallest useful set of issue titles. Merge duplicates that share the same root cause.
- Keep effort estimates coarse: `Small (< 1hr)`, `Medium (1-4hr)`, `Large (> 4hr)`.
- Make the action order explicit when one item unlocks another.
- Call out quick wins separately when they have high impact and low effort.
- Keep the report grounded in observed files, commands, and cited docs rather than generic advice.
