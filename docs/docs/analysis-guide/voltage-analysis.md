# Voltage Analysis

The Voltage Analysis tool provides a statistical view of how voltage is behaving downstream of a specific asset.

## Running the Analysis

1. Select a node on the map (e.g., a **Distribution Transformer**).
2. Right-click and select **Run Voltage Analysis**, or open the **Analytics Panel** from the sidebar.
3. The analysis runs automatically using the date range configured in **Global Settings** (gear icon in the toolbar).
4. To adjust the downstream scope, click **Filters** to expand the filter panel and change the **Search Depth**.

> **Large Dataset Warning**: If the query scope exceeds 10 million readings, the system will pause and display a capacity warning. Click **EXECUTE_QUERY_PLAN** to proceed, or **ABORT_ADJUST** to cancel and narrow the scope.

## Understanding the Results

The results are displayed in a floating, resizable window containing three synchronized charts.

### Distribution (KDE)
This chart shows a smoothed distribution of readings at different voltage levels, broken down by Phase (A, B, C).
- **Narrow Peak**: Indicates stable voltage regulation.
- **Wide/Multiple Peaks**: Suggests excessive voltage drop or poor regulation.

### Daily Voltage Stability (Median & 10/90 Bands)
Shows the **Daily Median**, **P10**, and **P90** voltage levels over the selected date range.
- **In-Band**: Generally between 114V and 126V (0.95 - 1.05 pu).
- **Wide P10/P90 spread**: Indicates high day-to-day voltage variability.

### Voltage vs Loading (Heatmap)
A scatter heatmap showing the relationship between total downstream loading (kWh) and Phase A voltage.
- Use this to identify if voltage sag correlates specifically with high load periods.

## Search Depth

The **Search Depth** filter in the Filters panel controls how far downstream the analysis traverses:

| Option | Behavior |
| :--- | :--- |
| **Strictly Downstream** | Traverses the entire downstream tree from the selected node. |
| **1–10 Degrees** | Limits traversal to the specified number of hops from the selected node. |
