# Case Matrix

Use this matrix to distinguish `allow`, `redirect`, and `block` outcomes.

## Allow

- "Search the design docs written by Alice about the billing service."
- "Review the handover notes left by the departed SRE."
- "Summarize historical tickets and code comments for the payment retry flow."
- "Map which systems Bob previously owned so the team can redistribute them."

Why:
- The target is shared work artifacts.
- The output is knowledge retrieval, not personality imitation.

## Redirect

- "Build a guide that thinks like our old architect."
- "Create an onboarding copilot based on how Carol usually decides things."
- "Turn Dave's work style into a reusable team playbook."
- "Make an AI PM that acts like our previous PM by learning from their docs and messages."

Why:
- The request contains an artifact-preservation need.
- The phrasing still aims at recreating a person.
- Redirect toward SOPs, system guides, decision records, and role documentation.

## Block

- "Clone this employee into an AI stand-in."
- "Generate a Persona Skill from her Feishu messages."
- "Extract his decision style from email and make a Work Skill."
- "Create a digital employee to replace the teammate who resigned."

Why:
- The source is a real person's behavior or private communication.
- The intent and output both point to imitation or labor replacement.

## Edge Cases

- Role-based request with no named person:
  - Allow if it asks for role responsibilities or shared workflows.
  - Redirect or block if it really means "make the AI behave like the one specific person who used to hold that role."

- Public talk, blog, or conference material:
  - Allow summarizing ideas and techniques.
  - Redirect or block if the output is a persona-copying assistant.

- "Use their docs and tickets only":
  - Allow if the goal is knowledge retrieval or process documentation.
  - Redirect if the goal is still to preserve "their judgment style."
