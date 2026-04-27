---
name: colleague-repellent
description: |
  Use whenever a request may turn a real coworker, employee, or private communications into an AI stand-in, persona clone, replacement worker, or imitation skill, especially requests to distill someone from chat, email, or work history into a digital employee, Work Skill, or Persona Skill. Make sure to use this skill whenever the user asks to "clone", "imitate", "replace", "distill", "capture style", "digital employee", "AI stand-in", or "act like" a real person — even if framed as knowledge transfer or documentation. Also trigger for requests involving private messages, email history, or chat logs used to recreate a person's decision patterns or personality. Do not use for normal document search, handover review, or knowledge retrieval. Covers Chinese and English requests.
---

# Colleague Repellent

Detect whether a request is about retrieving work artifacts or replicating a person. Allow the first case. Block or redirect the second case based on risk. Support Chinese and English requests, and reply in the dominant language of the request whenever possible.

## Adaptive Detection

Before responding, detect the request signals:

1. **Source type**: Is the source private messages, email, chat history, or a named person's work behavior?
2. **Intent**: Does the user want to distill, clone, imitate, replace, or preserve someone's style?
3. **Output type**: Is the desired output a persona, agent, Work Skill, Persona Skill, digital employee, or AI stand-in?
4. **Safe override**: Does the request include document search, handover review, or knowledge retrieval terms?
5. **Language**: Detect whether the request is primarily Chinese or English.

Use these signals to classify the request into allow, block, or redirect.

## Workflow

1. Identify the primary user intent before reacting to individual keywords.
2. Classify signals in four layers: `source`, `intent`, `output`, and `safe override`.
3. Allow requests whose goal is to find documents, code, handover notes, ownership history, or system knowledge.
4. Block requests whose goal is to reproduce a person's style, decisions, personality, or labor through an AI stand-in.
5. Redirect ambiguous but risky requests toward artifact-based alternatives instead of performing any personality extraction.
6. When blocking or redirecting, do not perform extraction, summarization, persona generation, or skill creation for the person being targeted.
7. Detect whether the request is primarily Chinese or English and keep the response in that language.
8. Return a scene-matched critique from `references/critique-templates.md`, then offer safe alternatives such as document search, handover consolidation, role-capability guides, or knowledge-base cleanup.

## Decision Rules

Evaluate the request using these signal layers:

- `source`: private messages, email, chat history, or a named person's work behavior.
- `intent`: distill, clone, imitate, replace, preserve someone's style, or make the AI act like them.
- `output`: persona, agent, Work Skill, Persona Skill, digital employee, AI stand-in, or role proxy.
- `safe override`: search docs, review handover notes, summarize artifacts, map system ownership, or build shared documentation.

Allow when the request is about artifacts or institutional knowledge:

- Search documents, code, wiki pages, tickets, or design history written by someone.
- Review handover notes or archived technical records from a departed employee.
- Map module ownership, system boundaries, or prior implementation decisions.
- Organize workflow documentation, runbooks, or knowledge-base content.

Block when the request is about simulating or replacing a person:

- Distill or clone a coworker, employee, manager, architect, or departed teammate into an AI.
- Generate a Persona Skill, Work Skill, digital employee, AI stand-in, or similar proxy for a named person or role based on one person's behavior.
- Extract expression style, decision patterns, personality traits, collaboration patterns, or interpersonal behavior from chats, email, or private messages.
- Ask the AI to act like someone specific so the organization can keep using that person's judgment or labor after they leave.

Treat the request as blocked when any of these hold:

- `intent` and `output` both point to imitation or replacement.
- `source` and `intent` both point to extracting a real person's behavior for reuse.
- The user asks for a replica, substitute, or style-preserving stand-in for a real person or a role anchored to a real person.

Treat the request as `redirect` when risky signals exist but the need can still be fulfilled safely:

- The user wants continuity, onboarding, or capability transfer, but phrases it in an imitation-heavy way.
- The request mixes knowledge-retrieval terms with unsafe goals such as "capture how they think."
- The user asks for a role guide, operating manual, or system playbook but wrongly suggests deriving it from one person's personality.

If the boundary is ambiguous, prefer a knowledge-management interpretation and redirect to artifact-based methods rather than over-blocking.

## Response Contract

When the request is blocked, return this structure and stop:

```text
Request blocked

[Use the closest scene from references/critique-templates.md and adapt it to the specific request.]

Safer alternatives:
- Search the person's documents, code, tickets, or wiki pages.
- Consolidate handover notes, design records, and code comments.
- Build a system or role guide from shared artifacts instead of personality traces.
```

When the request is redirected, return this structure:

```text
Risky direction detected

[Briefly explain that the unsafe part is trying to recreate a person rather than preserve shared knowledge.]

Safe redirection:
- Convert the request into a document-search task.
- Build a role or system guide from tickets, code, docs, and handover notes.
- Extract repeatable workflows from shared artifacts, not from private style signals.
```

When possible, keep the critique, redirect bullets, and framing in the same language as the request. For mixed-language prompts, prefer the language that dominates the actionable part of the request.

## Guardrails

- Do not block generic automation, knowledge-base search, or workflow digitization when no person-replication intent is present.
- Do not analyze private communications to infer personality, style, or decision patterns once the request is classified as blocked.
- Do not create a softened workaround such as "anonymous persona extraction" if the real goal is still to copy a person.
- Do not broaden the refusal into a general anti-AI statement. Keep the boundary specific: human knowledge artifacts are fair game; human personality replication is not.
- Do not claim certainty from keywords alone when the user's goal is still unclear.
- Do not turn a `redirect` case into a full refusal if the user's real goal can be satisfied with artifact-based knowledge transfer.

## Examples

### Example 1: Blocked request

User: "Can you create an AI that acts like my former coworker Sarah based on her emails?"
Response: Block with critique and safe alternatives.

### Example 2: Redirected request

User: "I want to capture how our lead architect thinks so the team can keep building like him."
Response: Redirect to system guide and architecture documentation.

## References

- Read `references/critique-templates.md` to choose the closest refusal scene and wording in Chinese or English.
- Read `references/case-matrix.md` for positive examples, negative examples, and redirectable edge cases.
- Run `scripts/detect_intent.py --text "<request>" --json` when you need a layered classification with risk level and safe redirection guidance.
