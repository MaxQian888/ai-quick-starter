# React Flow Quickstart And State

## Setup Truth

- Current package name: `@xyflow/react`
- Required style import: `@xyflow/react/dist/style.css`
- The React Flow wrapper must have explicit width and height, or the canvas will not render correctly.
- If the app uses Tailwind CSS 4, import the React Flow stylesheet after `tailwindcss` in a global stylesheet rather than from `App.tsx`.

## Default Product Baseline

Prefer a controlled flow for real product work:

- Keep `nodes` and `edges` in state.
- Wire `onNodesChange` through `applyNodeChanges`.
- Wire `onEdgesChange` through `applyEdgeChanges`.
- Wire `onConnect` through `addEdge`.

Use uncontrolled flow props such as `defaultNodes` and `defaultEdges` only for tiny demos, playgrounds, or intentionally self-contained examples.

## When To Escalate State Management

Local component state is enough when:

- the flow is isolated,
- node UI does not need to update sibling or global state,
- and there is no large editor shell around the canvas.

Move nodes, edges, and actions into Zustand or the repo's existing store when:

- custom nodes need to trigger graph-wide updates,
- side panels or toolbars must react to flow changes,
- derived selections or computed data need stable shared ownership.

When updating node data, create new objects all the way down:

```ts
set({
  nodes: get().nodes.map((node) =>
    node.id === nodeId
      ? { ...node, data: { ...node.data, color } }
      : node,
  ),
});
```

Do not mutate existing node or edge objects in place.

## useReactFlow

Use `useReactFlow()` when you need imperative reads or viewport actions without re-rendering the caller on every node or edge change.

Use it for:

- `fitView`, `zoomTo`, and viewport control,
- querying `getNodes()` or `getEdges()` on demand,
- update helpers that belong near flow-local orchestration logic.

Remember:

- It only works under `ReactFlow` or `ReactFlowProvider`.
- The instance is not ready during the very first render, so include it in callback dependencies.

## Official Docs

- Quick Start: https://reactflow.dev/learn
- State Management: https://reactflow.dev/learn/advanced-use/state-management
- `useReactFlow()`: https://reactflow.dev/api-reference/hooks/use-react-flow
