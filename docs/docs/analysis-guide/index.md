# Grid Analysis Guide

This guide explains how to interact with the interactive grid map and run various analytical use cases.

## Interacting with the Grid

- **Zoom & Pan**: Use your mouse or trackpad to navigate the 12,000+ node model.
- **Node Selection**: Click on any node (Substation, Transformer, Meter, or Switch) to see its details.
- **Context Menu**: Right-click on a node to access analysis shortcuts:
  - **Trace Downstream**: Highlights all assets logically "below" this node in the grid hierarchy.
  - **Trace Upstream**: Traces the path back to the Substation.
  - **Run Voltage Analysis**: Opens the detailed voltage distribution panel.
  - **Run Phase Balance**: Analyzes current and energy imbalance across phases.

## Available Analysis Types

1. [**Voltage Analysis**](./voltage-analysis.md): Statistical distribution of voltage readings over time.
2. [**Phase Balance (Load Flow)**](./load-flow.md): Comparison of loading across Phase A, B, and C.
3. [**Voltage Map (Heatmap)**](./voltage-map.md): System-wide visualization of voltage health.

## Degrees of Separation

Most analysis types allow you to specify **Degrees of Separation**. This controls how "deep" the search goes:
- **0 Degrees**: Only analyzes the selected node.
- **5 Degrees (Default)**: Analyzes the node and its immediate neighbors up to 5 steps away.
- **Full Trace (null)**: Analyzes the entire downstream tree from the selected point.
