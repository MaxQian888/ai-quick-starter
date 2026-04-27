---
name: develop-react-flow-projects
description: Use whenever building, migrating, or debugging React Flow projects, creating node-based UIs, flow diagrams, graph editors, canvas applications, or visual workflow tools. Make sure to use this skill for any request involving @xyflow/react, reactflow, custom nodes and edges, auto-layout engines, flow state management, or canvas performance tuning. Also triggers for blank canvas issues, React Flow version upgrades, connection rules, edge labels, viewport controls, or integrating Zustand with flow state.
---

# Develop React Flow Projects

## Overview

Inspect the current React Flow surface first, then make the narrowest change that fits the existing app. Use the bundled references to avoid common breakages around package version, controlled state, custom node wiring, layout engines, and performance.

## Adaptive Detection

Before changing code, scan the workspace to understand the current React Flow setup:

1. Detect package and version:
   - Check `package.json` for `@xyflow/react` (v12) vs legacy `reactflow` (v11 and earlier).
   - Note the installed version to avoid mixing incompatible APIs.
2. Detect existing flow patterns:
   - Search for `<ReactFlow` usage to find controlled vs uncontrolled setups.
   - Look for `nodeTypes`, `edgeTypes` declarations.
   - Check for Zustand stores or context providers holding flow state.
3. Detect styling and layout:
   - Look for CSS imports (`@xyflow/react/dist/style.css` or similar).
   - Check for layout engine usage (`dagre`, `elkjs`, `d3-hierarchy`, `d3-force`).
4. Detect build toolchain:
   - Check for Vite, Next.js, or CRA configurations that may affect bundling.

## Workflow

1. **Audit the current surface** before changing code.
2. **Choose the smallest seam** that matches the requested work.
3. **Implement** in the library's preferred patterns.
4. **Verify** the interaction paths that can actually regress.

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

## Examples

### Example 1: Adding a Custom Node Type

**Input:** "I need a node that shows a progress bar."

**Output:**
- Custom node component with `NodeProps` and `Handle` imports.
- Registered in `nodeTypes` outside render.
- Immutable update pattern via `useReactFlow().setNodes()` or store action.

### Example 2: Fixing a Blank Canvas

**Input:** "My flow canvas is blank after upgrading."

**Output:**
- Check CSS import order and parent container dimensions.
- Verify `@xyflow/react` vs `reactflow` imports match the installed version.
- Confirm controlled state props are wired correctly.

## Reference Map

- Read [references/quickstart-and-state.md](references/quickstart-and-state.md) for setup, controlled flows, CSS order, and store patterns.
- Read [references/custom-nodes-and-edges.md](references/custom-nodes-and-edges.md) for custom nodes, handles, edge types, and interaction classes.
- Read [references/layout-performance-and-migration.md](references/layout-performance-and-migration.md) for layout selection, performance guardrails, and v12 migration traps.

## Reporting

- Distinguish library constraints from product bugs.
- Say which flows, routes, gestures, or state transitions you actually verified.
- If the repo stays on an older React Flow line, say so explicitly instead of silently mixing APIs.
