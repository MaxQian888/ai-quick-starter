# Sub-Skill Generation

Use this file when creating the execution-focused child skill after the phase plan is stable.

## Goal

Create a small child skill that can resume work from `docs/progress/MASTER.md` and execute the planned phases without recreating the large planning workflow.

## Child-Skill Contract

The generated child skill must:

- read `docs/progress/MASTER.md` first in every new session,
- identify the active phase and the relevant phase file,
- execute only the next coherent task or checkpoint,
- preserve the verification boundaries defined by the phase plan,
- update the phase file immediately after finishing a task,
- let the main thread reconcile `MASTER.md`,
- and trigger cleanup behavior when all tracked tasks are complete.

## Generation Rules

1. Ask where the child skill should be installed.
2. Reuse the local skill-creation tooling when available.
3. Keep the child skill focused on the actual repository and plan. Do not ship a generic "do software development" template.
4. Encode:
   - the resume-first rule,
   - the current project scope,
   - the phase-file update behavior,
   - the verification boundary language,
   - and the cleanup trigger.
5. Keep the child skill lean. Detailed phase templates belong in `docs/progress/`, not in the child skill.

## What Not To Do

- Do not copy the full planning workflow into the child skill.
- Do not describe all future phases inline if `docs/progress/` already carries that detail.
- Do not hard-code platform-only instructions unless the child skill is intentionally platform-specific.
- Do not generate a child skill before the phase files exist on disk.
