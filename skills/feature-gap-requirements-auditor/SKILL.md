---
name: feature-gap-requirements-auditor
description: Use whenever comparing documentation against implementation to find missing or incomplete functionality, auditing feature completeness, verifying spec coverage, or generating requirement checklists from observed gaps. Make sure to use this skill for requirements audits, feature gap analysis, documentation-vs-code verification, compliance checking, or any request involving identifying what a component or folder should do but doesn't yet. Also triggers for spec completeness reviews, acceptance criteria generation from gaps, or contract metadata auditing.
---

# Feature Gap Requirements Auditor

Compare documentation signals against a narrow implementation surface before proposing new work. Use the helper script to collect docs, source files, tests, and keyword overlap first, then turn that evidence into a requirements list.

## Adaptive Detection

Before auditing, scan the workspace to understand the documentation and implementation landscape:

1. Detect available documentation:
   - Look for `README.md`, `spec.md`, `docs/`, `requirements/`, or `design/` directories.
   - Check for `SKILL.md`, `AGENTS.md`, or `CLAUDE.md` files that may contain requirements.
   - Search for `.md` files mentioning the target component or feature.
2. Detect implementation surface:
   - Identify the target directory or file from the user's request.
   - Look for corresponding test files to understand expected behavior.
3. Detect project conventions:
   - Check for existing requirement formats or ticket templates.
   - Look for priority labels or severity conventions used in the project.

## Workflow

1. Confirm the repository root and the exact target directory or file.
2. If the relevant requirements live outside the target subtree, pass them explicitly with repeated `--doc` flags.
3. Leave contract-style metadata out by default. Only add `--include-contract-requirements` when the user explicitly wants to audit package or skill contract completeness, not just feature gaps.
4. Run the audit before reading many implementation files:

```bash
uv run --python 3.11 scripts/build_feature_gap_audit.py --root <repo> --target <dir-or-file> [--doc <path>]...
```

Use `--include-contract-requirements` only when metadata like `display_name`, `description`, validation tasks, or file-contract items should be audited too.

5. Read the JSON output first. Use the Markdown output for a human-readable summary.
6. Separate the gap candidates by status:
   - `missing`: documented behavior has no convincing signal in the target surface.
   - `partial`: some related signals exist, but the documented behavior still looks incomplete.
   - `covered`: enough local signals exist that the requirement should not be reported as missing.
   - `uncertain`: the documentation or matching signal is too weak to support a confident claim.
7. Read `guardrail_findings` separately from feature gaps. Guardrails should not be promoted into missing functionality unless the user explicitly asks for policy or contract auditing.
8. Build the final answer from `missing` and `partial` capability items only.
9. Keep `covered` and `uncertain` items out of the main missing-feature list unless direct file reads prove the script wrong.

## What To Read In The Report

- `discovered_docs`: which docs actually informed the audit.
- `doc_requirements`: requirement-like statements extracted from those docs.
- `guardrail_findings`: negative rules and safety constraints found in the docs.
- `target_summary` and `target_files`: what implementation surface was scanned.
- `feature_gap_candidates`: the status and evidence for each documented requirement.
- `detailed_requirements`: pre-shaped requirements with rationale and acceptance criteria.
- `blind_spots`: reasons the audit may under- or over-report gaps.
- `suggested_next_reads`: the smallest next file set to inspect manually.

## Answering Rules

- Treat the script as a narrowing tool, not as final product truth.
- Treat ancestor `AGENTS.md` and `CLAUDE.md` as context by default; they are not primary feature-contract sources unless passed explicitly.
- Report confirmed missing functionality only from `missing` items, or from `partial` items after you inspect the owning files directly.
- When docs are weak or absent, say so plainly and downgrade the result to assumptions or follow-up questions.
- Convert each accepted gap into a requirement entry with:
  - feature title,
  - priority,
  - evidence,
  - concrete acceptance criteria,
  - open questions when ownership or behavior is still ambiguous.
- Prefer repo-truthful wording such as "documentation suggests" or "the target surface does not show" when runtime proof is missing.

## Examples

### Example 1: Component Audit

**Input:** "Audit the auth component against the spec."

**Output:**
- Discovers `spec.md` and `src/components/auth/`.
- Reports missing OAuth provider support and partial role-based access.
- Generates requirement checklist with acceptance criteria.

### Example 2: Skill Contract Audit

**Input:** "Check if this skill folder meets all contract requirements."

**Output:**
- Uses `--include-contract-requirements`.
- Audits `display_name`, `description`, and required file presence.
- Reports missing `evals/` directory and incomplete test coverage.

## Guardrails

- Do not invent features that are not documented or strongly implied by surrounding tests and exports.
- Do not mix guardrails, metadata, or package-contract items into the user-facing missing-feature list unless the request explicitly asks for them.
- Do not claim a gap is definitely missing if the report marks it `uncertain`.
- Do not treat keyword overlap as runtime proof.
- Do not widen from one component or folder into a whole-product rewrite unless the user asks.
- Do not hide blind spots; surface them with the requirement list.

## References

- Read [references/analysis-playbook.md](references/analysis-playbook.md) for document selection, status interpretation, and answer-shaping rules.
- Read [references/output-schema.md](references/output-schema.md) for the report contract emitted by the helper script.
