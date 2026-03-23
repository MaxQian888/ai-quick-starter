# Representative Official Or Commercial Platform Cards

Date: 2026-03-20
Source track: explorer-commercial
Status: baseline cards completed from official sources

## OpenAI Agents SDK

- Positioning: OpenAI's official code-first agent framework for tool-using, stateful, multi-agent applications.
- Primary tag: `tool-first-or-code-first`
- Verified:
  - Supports code-driven orchestration plus LLM-driven delegation via handoffs and agents-as-tools.
  - Supports function tools, MCP server tools, and hosted tools such as web search, file search, computer use, and code execution.
  - Built-in sessions support multiple state backends including SQLite, Redis, SQLAlchemy, Dapr, and OpenAI Conversations API.
  - Tracing is first-class and documented as built in.
  - Official Python and JS/TS surfaces are both public and documented.
- Inferred:
  - Lock-in is moderate rather than low if teams depend heavily on OpenAI-hosted tools or platform-specific state features.
- Strengths:
  - Clean orchestration primitives.
  - Strong tracing and session model.
  - Good fit for coding-agent orchestration and research/report workflows.
- Constraints:
  - Not a managed runtime.
  - Enterprise ops and governance stay with the application team.
- Sources:
  - https://openai.github.io/openai-agents-python/
  - https://openai.github.io/openai-agents-python/multi_agent/
  - https://openai.github.io/openai-agents-python/sessions/
  - https://openai.github.io/openai-agents-python/tracing/
  - https://github.com/openai/openai-agents-python
  - https://openai.github.io/openai-agents-js/
  - https://github.com/openai/openai-agents-js

## Azure AI Foundry Agent Service

- Positioning: Microsoft's managed agent platform focused on enterprise-hosted runtime, security, observability, and distribution.
- Primary tag: `enterprise-or-hosted`
- Verified:
  - Supports prompt agents, workflow agents, and hosted agents in the current docs.
  - Tool catalog includes web search, code interpreter, file search, and function calling.
  - Docs surface built-in memory/runtime capabilities and Azure resource integration.
  - Current lifecycle explicitly includes build, test, trace, evaluate, publish, and monitor.
  - Managed hosting, scaling, identity, and security are core value propositions.
- Inferred:
  - Lock-in is high in practice because the strongest deployment story is Azure-native.
- Strengths:
  - Strongest enterprise-hosted posture in this representative set.
  - Clear operational/governance story.
- Constraints:
  - Product naming and migration surface are still moving.
  - Some important capabilities remain preview.
- Sources:
  - https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview
  - https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-catalog
  - https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept
  - https://learn.microsoft.com/en-us/azure/ai-foundry/agents/whats-new

## Google Agent Development Kit

- Positioning: Google's official open-source, code-first, multi-language agent framework with a strong path to Google Cloud deployment.
- Primary tag: `tool-first-or-code-first`
- Verified:
  - Supports sequential, parallel, and loop workflow agents, plus multi-agent composition.
  - Tool ecosystem covers prebuilt tools, custom functions, third-party libraries, and agents-as-tools.
  - Session, state, and memory are documented as separate concepts with multiple implementations.
  - Built-in evaluation is explicitly documented.
  - Deployment docs cover Vertex AI Agent Engine, Cloud Run, GKE, and generic containers.
  - Official repo is Apache-2.0 licensed.
- Inferred:
  - Lock-in is lower than Azure's managed service, but rises when teams standardize on Gemini or Vertex AI Agent Engine.
- Strengths:
  - Best official/commercial entrant here for open, code-first orchestration.
  - Strong workflow and multi-agent primitives.
- Constraints:
  - Less turnkey than Azure for enterprise runtime governance.
  - Surface area is broad and moving quickly.
- Sources:
  - https://google.github.io/adk-docs/
  - https://google.github.io/adk-docs/agents/multi-agents/
  - https://google.github.io/adk-docs/sessions/
  - https://google.github.io/adk-docs/evaluate/
  - https://google.github.io/adk-docs/deploy/
  - https://github.com/google/adk-python
