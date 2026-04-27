# Scan Guardrails

Read narrowly and stop early.

## Skip By Default

Skip these unless the current task explicitly needs them:

- `_tmp*`
- `tmp`
- `node_modules`
- `.uv-cache*`
- `.uv-python`
- `__pycache__`
- generated `artifacts/`
- binary outputs or vendor directories

## First Pass

Start with:

1. repository root guidance,
2. helper scan output,
3. top candidate modules only.

Do not broaden into deep recursive reads on the first pass.

## When To Narrow Instead Of Read More

Rerun the helper script with `--include`, `--exclude`, or `--limit` when:

- too many modules look plausible,
- the current task targets one family of skills,
- generated or irrelevant modules are crowding the result.

Add `--task` when the current session goal is already concrete and you need better ranking without widening the read surface.

## Stop Conditions

Stop scanning and move to synthesis when:

- you can name the best first files to read next,
- you can state the main constraints confidently,
- additional examples would repeat the same lesson.

Stop and ask the user when:

- the task target is unclear,
- selected examples disagree materially,
- repository signals are too weak to support a trustworthy context pack.
