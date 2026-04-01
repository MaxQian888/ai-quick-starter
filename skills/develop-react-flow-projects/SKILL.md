---
name: develop-react-flow-projects
description: Guide Codex through building, extending, migrating, and debugging React Flow projects with @xyflow/react. Use when working on flow editors, node-edge canvases, drag-and-drop graph UIs, custom nodes or edges, layout engines, shared React Flow state, performance tuning, or migrations from legacy reactflow APIs.
---

# Develop React Flow Projects

## Overview

Inspect the current React Flow surface first, then make the narrowest change that fits the existing app. Use the bundled references to avoid common breakages around package version, controlled state, custom node wiring, layout engines, and performance.

## Workflow

1. Audit the current surface before changing code.
2. Choose the smallest seam that matches the requested work.
3. Implement in the library's preferred patterns.
4. Verify the interaction paths that can actually regress.

## Audit First

- Check whether the project uses legacy `reactflow` imports or current `@xyflow/react`.
- Check where the stylesheet is imported and whether the canvas parent has explicit width and height.
- Check whether the flow is controlled (`nodes`, `edges`, `onNodesChange`, `onEdgesChange`) or uncontrolled (`defaultNodes`, `defaultEdges`).
- Check where `nodeTypes`, `edgeTypes`, layout helpers, and shared graph state live.
- Preserve the current major version unless the user explicitly asked for migration.

## Pick The Seam

- Read `references/quickstart-and-state.md` before bootstrapping a new canvas, moving flow state into a store, or fixing blank-canvas issues.
- Read `references/custom-nodes-and-edges.md` before changing node components, handles, custom edges, connection rules, or edge labels and controls.
- Read `references/layout-performance-and-migration.md` before adding auto-layout, tuning large graphs, or touching upgrade paths from older React Flow versions.

## Implement Safely

- Default to a controlled flow for product code unless the task is a tiny demo.
- Update nodes and edges immutably; do not rely on object mutation.
- Declare `nodeTypes`, `edgeTypes`, and stable config objects outside render or memoize them.
- Memoize event handlers passed into `<ReactFlow />`.
- When node-local UI needs to change shared graph state, prefer a store action over threading callbacks through many `data` objects.

## Verify Common Failure Points

- Blank or broken canvas: verify CSS import order and explicit parent sizing first.
- Layout bugs on v12: use `node.measured?.width` and `node.measured?.height` for measured dimensions.
- Re-render storms: stop reading whole `nodes` or `edges` arrays in unrelated UI; prefer derived store fields or `useReactFlow()` for imperative reads.
- Reconnect regressions: use `onReconnect` and `reconnectEdge`, not removed `onEdgeUpdate` APIs.
- Shared-state bugs from custom nodes: confirm each node update creates a new node object and a new `data` object.

## Decision Guide

### Choose A State Model

- Stay with local component state for small editors and isolated prototypes.
- Move nodes, edges, and actions into Zustand or the repo's existing store when custom nodes need to update shared graph state from deep inside the tree.
- Use `useReactFlow()` for instance queries, viewport actions, and imperative helpers that should not re-render callers on every state change.

### Choose A Layout Strategy

- Use Dagre for directed trees and simple DAGs.
- Use D3-Hierarchy only when the graph is a single-root tree with near-uniform node sizes.
- Use D3-Force for organic or physics-like graphs and gate recomputation carefully.
- Use ELK when you need advanced routing, sub-flow awareness, or heavily configurable layout.

## Reference Map

- Read [references/quickstart-and-state.md](references/quickstart-and-state.md) for setup, controlled flows, CSS order, and store patterns.
- Read [references/custom-nodes-and-edges.md](references/custom-nodes-and-edges.md) for custom nodes, handles, edge types, and interaction classes.
- Read [references/layout-performance-and-migration.md](references/layout-performance-and-migration.md) for layout selection, performance guardrails, and v12 migration traps.

## Reporting

- Distinguish library constraints from product bugs.
- Say which flows, routes, gestures, or state transitions you actually verified.
- If the repo stays on an older React Flow line, say so explicitly instead of silently mixing APIs.
