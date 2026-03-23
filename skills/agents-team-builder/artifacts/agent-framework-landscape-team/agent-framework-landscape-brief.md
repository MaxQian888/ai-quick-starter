# Agent Framework Landscape Research Brief

We want to create a Codex agent team that researches the current agent-framework landscape and produces a practical decision package.

Deliverables:

- a normalized comparison matrix
- a ranked selection conclusion with recommended tiers
- a phased implementation roadmap for proof-of-concept and adoption

Constraints:

- use `agents-team-builder` to generate reviewable Markdown, JSON, and `.toml` drafts
- keep the team small
- prefer built-in Codex roles first, but add targeted custom roles when they materially reduce ambiguity
- research should be general-purpose rather than tied to one product
- open-source frameworks are the priority
- include a small number of representative official or commercial options for context
- target a standard-depth sample set of 12 to 15 frameworks total
- keep discovery parallel, but keep synthesis and recommendation serial after a clear merge point
- every conclusion must be evidence-backed and traceable to the matrix

Workflow expectations:

- stage 1 freezes the sample pool, evaluation criteria, and evidence standards
- stage 2 runs two parallel tracks: open-source research and representative official/commercial research
- stage 3 normalizes both tracks into one comparison matrix
- stage 4 produces the selection conclusion and the implementation roadmap
- final delivery should explicitly map typical use cases to recommended frameworks

Required research dimensions:

- orchestration model and control-flow expressiveness
- tool use and integration model
- memory, state, and persistence support
- multi-agent coordination support
- evaluation, observability, and debugging support
- production readiness and deployment options
- ecosystem maturity and documentation quality
- extensibility, vendor lock-in, and licensing posture
- fit for coding-agent orchestration, enterprise workflows, and research/reporting workloads

Suggested seed categories:

- graph or workflow orchestration frameworks
- multi-agent collaboration frameworks
- coding-agent or tool-first agent frameworks
- enterprise-friendly or hosted agent platforms

Suggested seed frameworks to validate or refine during stage 1:

- LangGraph
- CrewAI
- AutoGen
- Semantic Kernel
- PydanticAI
- smolagents
- LlamaIndex agent or workflow tooling
- Haystack agent tooling
- Mastra
- Agno
- OpenHands
- OpenAI Agents SDK
- one or two representative hosted or enterprise platforms chosen during stage 1

Team design goals:

- one lead or integration agent that owns criteria, merge points, and final review
- one open-source research agent
- one official or commercial research agent
- one analyst agent for matrix normalization
- one strategist agent for recommendation and rollout planning
