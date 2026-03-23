# Open-Source Agent Framework Cards

Date: 2026-03-20
Source track: explorer-open-source
Status: baseline cards completed from official sources

## LangGraph

- Positioning: low-level orchestration/runtime for long-running, stateful agents and workflows.
- Primary tag: `workflow-orchestration`
- Verified:
  - Graph-based orchestration supports branching, routing, parallelization, subgraphs, persistence, durable execution, interrupts, streaming, and memory.
  - Tool/model layer is flexible and does not strictly require LangChain.
  - Observability, studio, and deployment are strongly tied to LangSmith.
- Inferred:
  - Multi-agent support is compositional rather than a high-level team abstraction.
- Strengths:
  - Durable state and explicit control flow.
  - Strong production posture for resumable workflows.
- Constraints:
  - Lower-level than agent-first frameworks.
  - Best observability/deployment story leans commercial.
- Sources:
  - https://docs.langchain.com/oss/python/langgraph/
  - https://docs.langchain.com/oss/python/langgraph/workflows-agents
  - https://github.com/langchain-ai/langgraph/blob/main/README.md

## CrewAI

- Positioning: collaborative-agent framework centered on `Crews` plus event-driven `Flows`, with a strong enterprise upsell.
- Primary tag: `multi-agent-collaboration`
- Verified:
  - Crews, tasks, memory, knowledge, tools, MCP, and flows are first-class surfaces.
  - Flows provide shared state, branching, loops, and resumable execution.
  - Observability and production posture connect strongly to AMP or Control Plane.
- Inferred:
  - OSS core is useful, but the polished operational story increasingly centers on paid control-plane products.
- Strengths:
  - Clear multi-agent mental model.
  - Good enterprise/process-automation narrative.
- Constraints:
  - Production observability story is less self-contained in OSS.
- Sources:
  - https://docs.crewai.com/
  - https://docs.crewai.com/en/concepts/flows
  - https://docs.crewai.com/en/observability/overview
  - https://github.com/crewAIInc/crewAI/blob/main/README.md

## AutoGen

- Positioning: event-driven multi-agent framework stack with layered APIs, but no longer Microsoft's primary recommendation for new users.
- Primary tag: `multi-agent-collaboration`
- Verified:
  - Current README points new users toward Microsoft Agent Framework.
  - Core remains event-driven, distributed, observable/debuggable, and cross-language.
  - AgentChat, extensions, memory protocol, Bench, and Studio remain present.
- Inferred:
  - Strategic drift is now a larger concern than missing technical capability.
- Strengths:
  - Deep multi-agent architecture and distributed runtime.
- Constraints:
  - Forward-looking roadmap confidence is lower than before.
- Sources:
  - https://microsoft.github.io/autogen/stable/
  - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html
  - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
  - https://github.com/microsoft/autogen/blob/main/README.md

## Semantic Kernel

- Positioning: enterprise-oriented, model-agnostic SDK/orchestration framework for agents and multi-agent systems across C#, Python, and Java.
- Primary tag: `enterprise-or-hosted`
- Verified:
  - README positions SK as enterprise-ready for agents and multi-agent systems.
  - Tool or plugin model covers native code functions, prompt templates, OpenAPI, and MCP.
  - Supports vector DB integrations, local deployment, and a process framework for business workflows.
- Inferred:
  - Open-source and model-agnostic, but center of gravity remains Microsoft-leaning enterprise middleware.
- Strengths:
  - Cross-language support and enterprise posture.
- Constraints:
  - Documentation surface is split, and some Learn wording trails repo positioning.
- Sources:
  - https://learn.microsoft.com/en-us/semantic-kernel/overview/
  - https://github.com/microsoft/semantic-kernel/blob/main/README.md

## PydanticAI

- Positioning: type-safe Python agent or workflow framework centered on validated tools, structured outputs, evals, and durable execution.
- Primary tag: `tool-first-or-code-first`
- Verified:
  - First-party docs explicitly claim model-agnostic support, OTel or Logfire observability, evals, MCP, A2A, human approval, durable execution, streaming, and graphs.
  - Tooling is strongly typed and validation-centric.
- Inferred:
  - Multi-agent support is more protocol or graph driven than team-abstraction driven.
- Strengths:
  - Type safety, validation, strong Python ergonomics, and solid eval posture.
- Constraints:
  - Less obvious choice for large explicit multi-agent topologies.
- Sources:
  - https://ai.pydantic.dev/
  - https://github.com/pydantic/pydantic-ai/blob/main/README.md

## smolagents

- Positioning: minimal Hugging Face library for lightweight agents, especially code-writing agents, with strong portability.
- Primary tag: `tool-first-or-code-first`
- Verified:
  - Emphasizes simplicity, code agents, tool-calling agents, MCP interoperability, and model-agnostic operation.
  - Multi-agent hierarchies exist.
  - Local executor is explicitly not a security boundary.
- Inferred:
  - Memory and durable-state posture is lighter than orchestration-first systems.
- Strengths:
  - Fast to learn and highly portable.
- Constraints:
  - Production durability and governance are thinner than heavier frameworks.
- Sources:
  - https://huggingface.co/docs/smolagents/index
  - https://github.com/huggingface/smolagents/blob/main/README.md

## LlamaIndex

- Positioning: data-centric framework that now spans agents, workflows, and managed companion surfaces.
- Primary tag: `workflow-orchestration`
- Verified:
  - OSS docs position it around agents over your data, event-driven workflows, connectors, indexes, query engines, and observability or evaluation integrations.
  - LlamaAgents adds branching, parallelism, HITL review, durability, and observability.
- Inferred:
  - Multi-agent capability is increasingly split between OSS and companion products rather than one unified abstraction.
- Strengths:
  - Strong document and data ecosystem.
- Constraints:
  - Surface area and branding are fragmented.
- Sources:
  - https://docs.llamaindex.ai/en/stable/
  - https://developers.llamaindex.ai/python/llamaagents/overview/
  - https://github.com/run-llama/llama_index/blob/main/README.md

## Haystack

- Positioning: transparent Python orchestration framework for production RAG, agents, and context-engineered pipelines.
- Primary tag: `workflow-orchestration`
- Verified:
  - Docs describe Haystack as an open-source AI orchestration framework for production-ready agents, RAG, and multimodal search.
  - Agents, tools, memory, reasoning, and evaluation are explicit docs surfaces.
  - Evaluation is a first-class OSS feature.
- Inferred:
  - Agent story remains strongly grounded in explicit pipeline composition rather than opaque autonomy.
- Strengths:
  - Modularity, evaluation surface, and low lock-in.
- Constraints:
  - Less agent-identity-first than some team-centric frameworks.
- Sources:
  - https://docs.haystack.deepset.ai/docs/intro
  - https://docs.haystack.deepset.ai/docs/agents
  - https://docs.haystack.deepset.ai/docs/evaluation
  - https://github.com/deepset-ai/haystack/blob/main/README.md

## Mastra

- Positioning: TypeScript framework for shipping agents and workflows inside modern web or backend apps, with built-in memory, evals, and observability.
- Primary tag: `workflow-orchestration`
- Verified:
  - Docs and README position it across agents, workflows, memory, MCP servers, evals, and observability.
  - Workflows are graph-based with branching, parallelism, and suspend or resume via storage-backed state.
  - Observability traces model, agent, workflow, and memory operations.
- Inferred:
  - One of the stronger choices for TS-native product teams.
- Strengths:
  - Strong TS ergonomics and built-in batteries.
- Constraints:
  - Dual-license structure means not all production features are pure OSS.
- Sources:
  - https://mastra.ai/docs
  - https://mastra.ai/docs/agents/overview
  - https://mastra.ai/docs/observability/overview
  - https://mastra.ai/docs/memory/conversation-history
  - https://github.com/mastra-ai/mastra/blob/main/README.md

## Agno

- Positioning: agent runtime stack for building agents, teams, and workflows as scalable services with a bundled control-plane story.
- Primary tag: `multi-agent-collaboration`
- Verified:
  - Agno positions itself as framework plus runtime plus control plane.
  - Teams are first-class with multiple team modes and approval pauses.
  - Workflows support sequential, parallel, looped, and conditional steps.
  - Production posture includes stateless scale-out runtime and DB-backed state.
- Inferred:
  - More opinionated platform shape than lighter libraries.
- Strengths:
  - Explicit team orchestration and governance posture.
- Constraints:
  - Smaller ecosystem footprint than the largest incumbents.
- Sources:
  - https://docs.agno.com/introduction
  - https://docs.agno.com/teams
  - https://docs.agno.com/workflows
  - https://github.com/agno-agi/agno/blob/main/README.md

## OpenHands

- Positioning: open-source software-agent framework focused specifically on coding agents.
- Primary tag: `tool-first-or-code-first`
- Verified:
  - Current stack covers SDK, CLI, local GUI, cloud, and enterprise.
  - SDK includes coding tools, persistence, sub-agent delegation, context compression, security analysis, metrics, and OTEL tracing.
  - Persistence and parallel sub-agent delegation are explicitly documented.
- Inferred:
  - Clearer fit for coding-agent orchestration than for general enterprise workflow automation.
- Strengths:
  - Coding-specific tools and delegation model.
- Constraints:
  - Narrower domain focus than broader workflow frameworks.
- Sources:
  - https://docs.openhands.dev/sdk
  - https://docs.openhands.dev/sdk/guides/observability
  - https://docs.openhands.dev/sdk/guides/agent-delegation
  - https://docs.openhands.dev/sdk/guides/convo-persistence
  - https://github.com/All-Hands-AI/OpenHands/blob/main/README.md
