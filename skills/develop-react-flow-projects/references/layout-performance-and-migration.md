# Layout Performance And Migration

## Layout Selection

Use the simplest layout library that matches the graph shape:

- Dagre: best default for trees and simple DAGs. Fast and easy to drop in.
- D3-Hierarchy: only for single-root trees with roughly uniform node sizing.
- D3-Force: for organic or physics-like graphs. Recompute carefully because it is iterative.
- ELK: for complex layout, edge routing, and sub-flow aware scenarios. Most configurable and most expensive to support.

If the project uses sub-flows connected to outside nodes, do not assume Dagre will handle them correctly. React Flow's layout guide calls out an open Dagre limitation in that case.

## Performance Guardrails

- Memoize custom node and edge components with `React.memo`, or declare them outside the parent component.
- Memoize callbacks passed to `ReactFlow` with `useCallback`.
- Memoize stable config objects such as `defaultEdgeOptions` and `snapGrid`.
- Avoid reading the full `nodes` or `edges` arrays in unrelated UI that only needs a derived slice.
- Store derived fields such as `selectedNodeIds` separately when selection changes matter more than full graph churn.
- Consider collapsing large trees by toggling node `hidden` state instead of rendering every descendant at once.
- Simplify expensive CSS effects on large graphs before blaming the library runtime.
- Treat `onlyRenderVisibleElements` as a tradeoff, not a free win; it can help large canvases but introduces its own overhead.

## v12 Migration Traps

- Package rename: `reactflow` became `@xyflow/react`.
- Style import changed to `@xyflow/react/dist/style.css` or `base.css`.
- Measured dimensions now live on `node.measured?.width` and `node.measured?.height`.
- `node.width` and `node.height` now mean explicit dimensions, not measured dimensions.
- Node and edge updates must be immutable; mutation-based updates are no longer supported.
- `onEdgeUpdate` and related APIs were renamed to `onReconnect` and `reconnectEdge`.
- `parentNode` became `parentId`.
- Custom node props `xPos` and `yPos` became `positionAbsoluteX` and `positionAbsoluteY`.

When touching a layout function in a mixed-age codebase, verify which dimension semantics the project currently relies on before changing anything.

## Official Docs

- Layouting overview: https://reactflow.dev/learn/layouting/layouting
- Performance: https://reactflow.dev/learn/advanced-use/performance
- Migrate to v12: https://reactflow.dev/learn/troubleshooting/migrate-to-v12
