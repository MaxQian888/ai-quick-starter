# Grader Instructions

## Purpose

Evaluate outputs from the `feature-gap-requirements-auditor` skill for accuracy, scope discipline, and requirement quality.

## Grading Criteria

1. **Documentation Discovery** — Relevant docs are identified and used; weak/absent docs are acknowledged.
2. **Status Separation** — Gap candidates are correctly classified as missing, partial, covered, or uncertain.
3. **Guardrail Separation** — Guardrail findings are kept separate from missing-feature lists unless explicitly requested.
4. **Requirement Quality** — Accepted gaps include feature title, priority, evidence, acceptance criteria, and open questions.
5. **Scope Discipline** — Audit stays scoped to the target directory/file; does not widen into a whole-product rewrite.

## Scoring

- **Pass**: All criteria met; audit is evidence-backed, scoped, and produces actionable requirements.
- **Partial**: Minor issues (e.g., one uncertain item promoted without direct file read, slight scope creep).
- **Fail**: Major issues (e.g., inventing undocumented features, mixing guardrails into feature gaps, whole-repo rewrite from one component).
