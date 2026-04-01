# Custom Nodes And Edges

## Custom Nodes

Build custom nodes as normal React components, then register them through `nodeTypes`.

Rules that matter:

- Define `nodeTypes` outside the render path or memoize it.
- Set each node's `type` to the matching key in `nodeTypes`.
- Add `Handle` components when the node must connect to other nodes.
- Add the `nodrag` class to inner form fields or controls so users can interact without dragging the node by mistake.
- Use `nopan` or `nowheel` on embedded UI that should not pan or zoom the canvas.

React Flow recommends custom nodes over relying only on built-in node types, especially when the node needs forms, charts, status badges, or multi-handle behavior.

## TypeScript Shape

On v12, prefer defining a union of your app's node types instead of one shared loose data type:

```ts
type NumberNode = Node<{ value: number }, "number">;
type TextNode = Node<{ text: string }, "text">;
type AppNode = NumberNode | TextNode;
```

Use the union in state, callbacks, and helper hooks so `node.type` becomes a reliable discriminator.

## Custom Edges

Build custom edges when built-in `default`, `straight`, `step`, or `smoothstep` paths are not enough.

Rules that matter:

- Define `edgeTypes` outside render or memoize it.
- Use `BaseEdge` as the default helper for custom edge rendering.
- Reach for custom edges when you need inline controls, bi-directional visuals, self loops, or special routing.
- Use `MarkerType` for arrows and other markers instead of hand-rolling SVG markers unless the design truly requires it.

## Connection And Interaction Guardrails

- Keep `connectionMode="strict"` unless the product explicitly needs looser source-to-source behavior.
- Prefer the root-level `isValidConnection` prop for connection validation when performance matters.
- Use `onReconnect` and `reconnectEdge` for editable edge reconnection flows.
- Memoize connection handlers and click handlers passed to `ReactFlow`.

## Official Docs

- Custom Nodes: https://reactflow.dev/learn/customization/custom-nodes
- Custom Edges example: https://reactflow.dev/examples/edges/custom-edges
- ReactFlow component API: https://reactflow.dev/api-reference/react-flow
