---
name: software-research-tutorial-builder
description: |
  Use whenever you need evidence-backed software research tutorials that connect product context, docs, workflows, and practical adoption paths. Make sure to use this skill whenever the user says "tutorial", "getting started", "how to use", "research", "learn", "guide", "walkthrough", or "documentation" for a specific software product, library, framework, or tool — even for niche or emerging projects with limited docs. Also trigger when the user needs to onboard a team to a new technology, create internal training materials, or evaluate adoption feasibility. Covers open-source libraries, SaaS products, developer tools, cloud services, and programming languages.
---

# Software Research Tutorial Builder

## Overview

Research a software product in parallel, normalize the findings into one shared brief, then build a tutorial package with runnable steps and support materials.

Default to a two-stage flow: collect evidence first, synthesize tutorial assets second.

## Adaptive Detection

Before building a tutorial, detect the target context:

1. **Software type**: Is it a library, CLI tool, SaaS, framework, or cloud service?
2. **Version window**: Check for latest stable, LTS, or bleeding-edge requirements.
3. **Platform constraints**: Note OS, runtime, and dependency requirements.
4. **Learner level**: Determine if the audience is beginner, intermediate, or advanced.
5. **Existing docs**: Check official docs quality, community tutorials, and known gaps.

Use these signals to choose research depth, example complexity, and prerequisite list.

## Workflow

1. Define the software target, version window, operating systems, and learner goal in one short brief.
2. Dispatch parallel research tracks for official sources, community sources, and example design.
3. Read `references/workflow.md` before assigning track prompts or deciding merge points.
4. Read `references/source-policy.md` before accepting a claim into the shared brief.
5. Save structured findings from each track, then run:

```bash
python scripts/build_research_brief.py --input findings.json --format markdown --output research-brief.md
```

6. Review the generated brief for conflicts, missing prerequisites, platform differences, and unresolved questions.
7. Read `references/tutorial-contract.md` and `references/case-design.md` before drafting the tutorial.
8. Generate the tutorial outline:

```bash
python scripts/build_tutorial_outline.py --input research-brief.json --output tutorial-outline.md
```

9. Fill the tutorial sections, create the support materials, and mark which steps were directly verified.
10. State what remains source-backed but unverified in the final tutorial package.

## Required Research Tracks

### Official Track

Collect authoritative product facts:
- installation methods,
- version notes,
- feature boundaries,
- API or command references,
- and vendor-supported examples.

### Community Track

Collect practical usage evidence:
- real setup shortcuts,
- common failure modes,
- migration notes,
- examples from trusted repos,
- and recurring troubleshooting patterns.

### Case-Design Track

Plan the tutorial examples:
- one minimal runnable example,
- one practical workflow example,
- one troubleshooting case,
- and the support materials needed for each case.

## Output Contract

Every final deliverable should include:

1. a normalized research brief,
2. a tutorial outline,
3. a main Markdown tutorial,
4. a support-material checklist,
5. and a verification summary.

Read `references/tutorial-contract.md` for the required sections and asset expectations.

## Guardrails

- Do not let parallel agents write disconnected final tutorial chapters.
- Do not accept a community workaround without recording whether it conflicts with official guidance.
- Do not hide version uncertainty. Keep exact versions or date windows visible.
- Do not present a source-backed step as fully verified unless it was actually executed.
- Do not turn this skill into general market research or academic research. Keep the scope software-specific.
- Do not skip the troubleshooting case. A tutorial without failure recovery is incomplete.

## Examples

### Example 1: Build a research brief

```bash
python scripts/build_research_brief.py --input findings.json --format markdown --output research-brief.md
```

### Example 2: Generate tutorial outline

```bash
python scripts/build_tutorial_outline.py --input research-brief.json --output tutorial-outline.md
```

## References

- Read `references/workflow.md` for the staged multi-agent research flow.
- Read `references/source-policy.md` for evidence ranking, conflict handling, and freshness rules.
- Read `references/tutorial-contract.md` for required tutorial sections and package outputs.
- Read `references/case-design.md` for the minimal, practical, and troubleshooting case requirements.

## Helper Scripts

Use `scripts/build_research_brief.py` to merge track outputs into a shared brief.

Use `scripts/build_tutorial_outline.py` to turn a structured brief into a stable tutorial outline and support-material checklist.
