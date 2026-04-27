---
name: ai-research-writing
description: >
  Make sure to use this skill whenever the user needs help with academic writing,
  research paper drafting, LaTeX editing, Chinese-to-English or English-to-Chinese
  translation of papers, polishing de-AI text, or creating architecture diagrams
  and experiment visualizations. Also trigger for paper review feedback, reviewer
  response drafting, conference submission formatting, thesis chapter writing,
  or setting up AI-assisted research writing tools. Covers synonyms like
  "academic paper," "manuscript," "dissertation," "journal article," "research
  report," "paper revision," and "writing assistant." Use it even when the user
  only mentions "help me write" in a research or academic context.
---

# AI Research Writing

## Overview

Route broad academic-writing requests into the correct upstream prompt or external skill without making the user remember a long README. Keep the local package script-backed: use the routing script for task selection, the install script for environment setup, and the cache-sync script for the upstream source snapshot.

## Adaptive Detection

Before routing, detect the user's context:

- Identify the source language (Chinese or English) and target output format (LaTeX, Word, Markdown).
- Check if the request is about drafting, polishing, translating, reviewing, or tool setup.
- Scan `references/usage-map.md` for the local workflow map.
- Refresh `references/cache/upstream-awesome-ai-research-writing.md` if the cached content may be stale.

## Start Here

1. Run the workflow selector first when the request is broad or ambiguous:

```bash
python scripts/select_workflow.py --json "<user request>"
```

2. Read `references/usage-map.md` plus the matched upstream section from `references/cache/upstream-awesome-ai-research-writing.md`.
3. If the request is about environment setup or external capabilities, build the component installation plan:

```bash
python scripts/install_components.py --json all
```

4. Refresh the cached upstream README when section titles or prompt wording may be stale:

```bash
python scripts/sync_upstream_reference.py
```

## Prompt Routing

Use the selector output to pick the narrowest prompt family:

- `cn-to-en`: Chinese draft to English academic LaTeX.
- `en-to-cn`: English LaTeX to readable Chinese.
- `zh-refine`: Chinese rewriting, Word-friendly polishing, or Chinese de-AI cleanup.
- `en-refine`: English polishing, shortening, expanding, logic checks, or LaTeX de-AI cleanup.
- `visual-support`: architecture diagrams, chart recommendations, captions, and experiment analysis.
- `reviewer-audit`: harsh review report plus strategic revision advice.
- `skills-setup`: OpenSkills setup and curated external component installation.

Do not paraphrase the upstream prompt contract when a matching section already exists in the cached README. Reuse the section's role, task, constraints, and output format.

## Installation And External Components

When the user wants related writing components installed or configured:

1. Read `references/components-and-setup.md`.
2. Generate the plan with `scripts/install_components.py`.
3. Only run `--execute` after explicit user approval to modify the environment.
4. For `anthropics/skills`, install the repository and select only the requested skill names from the interactive picker.

## Guardrails

- Do not invent a new output schema when the cached upstream section already defines one.
- Do not auto-install OpenSkills or external skills unless the user explicitly asks to modify the environment.
- Do not assume the upstream README cache is current; refresh it when freshness matters.
- Do not widen a narrow writing request into a full-paper workflow unless the user asks.
- Do not treat Word and LaTeX outputs as interchangeable. Preserve the requested surface.

## Examples

**Polishing an English paper section:**
```bash
python scripts/select_workflow.py --json "Polish the introduction of my ML paper, make it more concise"
```
Then follow the `en-refine` route from `references/usage-map.md`.

**Setting up writing tools:**
```bash
python scripts/install_components.py --json all
```
Review the plan, then run with `--execute` after user approval.

## References

- Read `references/usage-map.md` for the local workflow map.
- Read `references/components-and-setup.md` for the curated install registry and verification rules.
- Read `references/cache/upstream-section-index.json` before searching the cached upstream README.
- Read `references/cache/upstream-awesome-ai-research-writing.md` when you need the full upstream section content.
