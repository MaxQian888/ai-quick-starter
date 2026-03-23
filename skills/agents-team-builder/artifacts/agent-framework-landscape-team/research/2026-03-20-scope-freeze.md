# Agent Framework Landscape Scope Freeze

Date: 2026-03-20
Owner: lead
Status: frozen for round 1 research

## Goal

Research the current agent-framework landscape and deliver:

- one normalized comparison matrix
- one ranked selection conclusion with recommended tiers
- one phased implementation roadmap

The research is general-purpose rather than tied to a single product, but the final package must still map frameworks to typical use cases.

## Sample Pool

Round 1 uses a 14-item pool.

### Open-Source Priority Set

1. LangGraph
2. CrewAI
3. AutoGen
4. Semantic Kernel
5. PydanticAI
6. smolagents
7. LlamaIndex
8. Haystack
9. Mastra
10. Agno
11. OpenHands

### Representative Official Or Commercial Context Set

12. OpenAI Agents SDK
13. Azure AI Foundry Agent Service
14. Google Agent Development Kit

## Category Tags

Each framework can carry more than one tag, but each item gets one primary tag for reporting:

- `workflow-orchestration`
- `multi-agent-collaboration`
- `tool-first-or-code-first`
- `enterprise-or-hosted`

Primary-tag assignments for round 1:

- LangGraph: `workflow-orchestration`
- CrewAI: `multi-agent-collaboration`
- AutoGen: `multi-agent-collaboration`
- Semantic Kernel: `enterprise-or-hosted`
- PydanticAI: `tool-first-or-code-first`
- smolagents: `tool-first-or-code-first`
- LlamaIndex: `workflow-orchestration`
- Haystack: `workflow-orchestration`
- Mastra: `workflow-orchestration`
- Agno: `multi-agent-collaboration`
- OpenHands: `tool-first-or-code-first`
- OpenAI Agents SDK: `tool-first-or-code-first`
- Azure AI Foundry Agent Service: `enterprise-or-hosted`
- Google Agent Development Kit: `tool-first-or-code-first`

## Research Dimensions

Every framework card must cover these dimensions:

1. Orchestration model and control-flow expressiveness
2. Tool use and integration model
3. Memory, state, and persistence support
4. Multi-agent coordination support
5. Evaluation, observability, and debugging support
6. Production readiness and deployment options
7. Ecosystem maturity and documentation quality
8. Extensibility, vendor lock-in, and licensing posture
9. Fit for coding-agent orchestration
10. Fit for enterprise workflow automation
11. Fit for research and report-generation workflows

## Evidence Rules

- Prefer official documentation, official GitHub repositories, and first-party changelogs.
- Use current sources dated or crawled recently enough to support a March 20, 2026 snapshot.
- Distinguish verified facts from inference.
- Record one source link per major claim cluster at minimum.
- If a framework surface is experimental, preview, or rapidly changing, label it explicitly.
- Do not normalize missing evidence into a positive rating.

## Output Contract

### Explorer Outputs

Each explorer writes framework cards with:

- framework name
- primary tag
- short positioning summary
- dimension-by-dimension findings
- notable strengths
- notable constraints
- licensing or lock-in notes
- recommended use cases
- source list

### Analyst Output

The analyst produces:

- one normalized matrix
- one gap log listing unclear or weakly evidenced areas

### Strategist Output

The strategist produces:

- recommendation tiers
- scenario-specific picks
- phased proof-of-concept to adoption roadmap

## Parallel Boundary

Safe to parallelize:

- open-source framework research
- representative official or commercial platform research

Must stay serial:

- sample-pool changes
- rubric changes
- matrix normalization
- recommendation writing
- final package review

## Merge Rule

The analyst starts only after both explorer tracks hand off cards that cover the full dimension set for every assigned framework.

## Notes For Round 1

- Open-source remains the center of gravity for final recommendations unless the evidence strongly favors an official or hosted option for a specific scenario.
- Official or commercial entries are included for contrast, operational maturity signals, and lock-in analysis rather than to dominate the shortlist.
