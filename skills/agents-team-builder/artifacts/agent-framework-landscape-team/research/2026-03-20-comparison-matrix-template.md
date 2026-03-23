# Agent Framework Landscape Comparison Matrix

Date: 2026-03-20
Status: template awaiting explorer findings

## Rating Scale

- `High`: strong first-party evidence and mature support
- `Medium`: usable support with clear limitations or narrower fit
- `Low`: limited, immature, or weakly evidenced support
- `Unknown`: not yet evidenced strongly enough for rating

## Matrix Columns

| Framework | Primary Tag | Orchestration | Tools | Memory/State | Multi-Agent | Evals/Observability | Production Posture | Ecosystem/Docs | Lock-In/Licensing | Coding Agents | Enterprise Workflows | Research Workflows | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LangGraph | workflow-orchestration | High | High | High | Medium | High | High | High | Medium | Medium | High | Medium | Strongest for stateful durable workflows; LangSmith gravity |
| CrewAI | multi-agent-collaboration | High | High | High | High | Medium | High | Medium | Medium | Medium | High | Medium | Team-centric mental model; AMP gravity for polished ops |
| AutoGen | multi-agent-collaboration | High | High | Medium | High | Medium | Medium | Medium | Low | Medium | Medium | Medium | Capable but roadmap risk because Microsoft points new users elsewhere |
| Semantic Kernel | enterprise-or-hosted | High | High | Medium | High | Medium | High | Medium | Medium | Medium | High | Medium | Enterprise middleware posture; strong plugin model |
| PydanticAI | tool-first-or-code-first | Medium | High | High | Medium | High | High | High | Low | Medium | Medium | High | Strong type-safety and eval posture for Python teams |
| smolagents | tool-first-or-code-first | Medium | High | Low | Medium | Low | Low | High | Low | Medium | Low | High | Lightweight and portable; thin durability story |
| LlamaIndex | workflow-orchestration | High | High | Medium | Medium | Medium | Medium | High | Medium | Medium | Medium | High | Data-centric with fragmented OSS vs cloud surface |
| Haystack | workflow-orchestration | High | High | Medium | Medium | High | Medium | High | Low | Medium | High | High | Transparent pipeline composition and strong eval surface |
| Mastra | workflow-orchestration | High | High | High | High | High | High | High | Medium | Medium | Medium | High | TS-native batteries-included option; dual-license caveat |
| Agno | multi-agent-collaboration | High | High | High | High | High | High | Medium | Medium | Medium | High | Medium | Runtime-plus-control-plane shape for governed self-hosting |
| OpenHands | tool-first-or-code-first | Medium | High | High | High | High | High | Medium | Medium | High | Low | Medium | Best fit for coding agents, not broad business workflows |
| OpenAI Agents SDK | tool-first-or-code-first | High | High | High | High | High | Medium | High | Medium | High | Medium | High | SDK, not managed runtime |
| Azure AI Foundry Agent Service | enterprise-or-hosted | High | High | Medium | High | Medium | High | Medium | High | Medium | High | Medium | Managed Azure platform; some surfaces still preview |
| Google Agent Development Kit | tool-first-or-code-first | High | High | High | High | High | High | High | Medium | Medium | Medium | High | Official open-source framework with strong deployment flexibility |

## Gap Log

- Open-source framework cards still pending from explorer-open-source.
- OpenAI Agents SDK and Google ADK were retagged from `enterprise-or-hosted` to `tool-first-or-code-first` based on official documentation.
