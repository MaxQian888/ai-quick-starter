# Agent Framework Landscape Recommendations

Date: 2026-03-20
Status: baseline recommendations from round 1 matrix

## Tiering

- Tier A:
  LangGraph, Mastra, PydanticAI, Agno, Google Agent Development Kit
- Tier B:
  Haystack, CrewAI, OpenAI Agents SDK, Semantic Kernel, OpenHands
- Tier C:
  LlamaIndex, smolagents, AutoGen, Azure AI Foundry Agent Service

## Why These Tiers

- Tier A frameworks combine strong first-party evidence with a clearer strategic fit:
  - LangGraph for durable, stateful orchestration
  - Mastra for TypeScript-native product teams
  - PydanticAI for typed Python workflows and evaluation-heavy development
  - Agno for governed self-hosted multi-agent services
  - Google ADK for official, code-first, multi-agent orchestration with flexible deployment
- Tier B frameworks are credible but narrower or more conditional:
  - Haystack is strong for explicit RAG or pipeline-heavy systems
  - CrewAI is strong for team-style business workflows but operationally leans toward AMP
  - OpenAI Agents SDK is excellent for code-first custom agents, but not a managed runtime
  - Semantic Kernel is solid for enterprise middleware, especially Microsoft-oriented stacks
  - OpenHands is excellent for coding agents but narrower outside software-task automation
- Tier C frameworks are not dismissed, but they carry stronger caution flags:
  - LlamaIndex has real power, but the OSS versus managed surface is fragmented
  - smolagents is attractive for small prototypes, but thinner on durability and governance
  - AutoGen remains capable, but roadmap drift lowers recommendation confidence for new adoption
  - Azure AI Foundry Agent Service is strong for managed enterprise hosting, but high lock-in and preview churn make it a contextual choice rather than a general default

## Scenario Picks

- Coding-agent orchestration:
  - Primary: OpenHands
  - Runner-up: OpenAI Agents SDK
  - Conservative Python option: PydanticAI
- Enterprise workflow automation:
  - Primary hosted option: Azure AI Foundry Agent Service
  - Primary self-managed option: Agno
  - Microsoft-stack SDK option: Semantic Kernel
- Research and report-generation workflows:
  - Primary general option: LangGraph
  - Lightweight code-first option: OpenAI Agents SDK
  - Google-leaning option: Google ADK
- TypeScript product teams:
  - Primary: Mastra
  - Runner-up: LangGraph if the team accepts a Python-heavy ecosystem
- Small-team experimentation:
  - Primary fast-start option: smolagents
  - Structured Python option: PydanticAI
- Retrieval-heavy or document-centric workflows:
  - Primary: Haystack
  - Runner-up: LlamaIndex

## Roadmap

### Phase 1: Shortlist Validation

- Freeze one representative proof-of-concept workflow with:
  - one tool call
  - one memory or state requirement
  - one evaluation or tracing requirement
  - one failure or recovery path
- Build a 3-framework shortlist by scenario:
  - General orchestration shortlist: LangGraph, Google ADK, PydanticAI
  - Enterprise shortlist: Agno, Azure AI Foundry Agent Service, Semantic Kernel
  - Coding-agent shortlist: OpenHands, OpenAI Agents SDK, PydanticAI

### Phase 2: Proof Of Concept

- Implement the same bounded workflow on each shortlisted framework.
- Compare:
  - control-flow clarity
  - tool integration effort
  - state and persistence ergonomics
  - tracing or observability quality
  - deployment friction
  - lock-in or licensing implications
- Keep the PoC narrow enough to finish in days, not weeks.

### Phase 3: Adoption Decision

- Pick one primary framework per target scenario rather than forcing one winner for every use case.
- Document fallback choices:
  - LangGraph or Google ADK for general orchestration
  - Agno or Azure AI Foundry Agent Service for governed enterprise delivery
  - OpenHands or OpenAI Agents SDK for coding-agent programs
- Define reevaluation checkpoints:
  - after first PoC
  - after first production-facing pilot
  - after major upstream roadmap changes

## Open Decisions

- Whether to keep a weighted numeric matrix or stay qualitative
- Whether Azure AI Foundry Agent Service should remain in the general pool or move to an enterprise-only appendix
- Whether AutoGen should be retained in future rounds now that Microsoft points new users toward a different forward path
