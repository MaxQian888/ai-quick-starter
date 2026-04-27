# Pattern Selection

Select a small set of examples that add distinct value to the current task.

## Choose Examples With Strong Evidence

Prefer modules that show several of these signals:

- precise trigger description in `SKILL.md`,
- concise workflow guidance,
- focused `references/`,
- deterministic helper scripts,
- tests that lock a behavior contract,
- stable output shape,
- explicit guardrails that prevent overreach.

## Default Selection Order

1. Read repository root guidance.
2. Run the helper scan.
3. Start with 2 strong examples.
4. Add more only when each added example contributes a new lesson.
5. Stop at 5 examples even in a large repository.

## Mix Examples Intentionally

Prefer a mix that matches the current task:

- script-backed skill plus script-backed skill when automation structure matters,
- script-backed skill plus document-first skill when output contract and reasoning style both matter,
- nearby domain examples before unrelated "best-looking" modules.

## Avoid Weak Selections

Do not choose examples only because they are:

- large,
- recent,
- personally familiar,
- artifact-heavy,
- under `_tmp*`, `tmp`, caches, or generated directories.

Do not treat neat folder structure alone as proof that a module is a strong success case.
