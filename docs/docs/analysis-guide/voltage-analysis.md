# Voltage Analysis

The Voltage Analysis tool provides a statistical view of how voltage is behaving downstream of a specific asset.

## Running the Analysis

1. Select a node on the map (e.g., a **Distribution Transformer**).
2. Open the **Analytics Panel** from the sidebar or right-click and select **Voltage Analysis**.
3. Select a **Date Range**.
4. Adjust the **Degrees of Separation** if needed.
5. Click **Run Analysis**.

## Understanding the Results

### Voltage Distribution (Histogram)
This chart shows the count of readings at different voltage levels, broken down by Phase (A, B, C).
- **Narrow Peak**: Indicates stable voltage regulation.
- **Wide/Multiple Peaks**: Suggests excessive drop or poor regulation.

### Voltage Timeseries
Shows the **Daily Median**, **P10**, and **P90** voltage levels over the selected range.
- **In-Band**: Generally between 114V and 126V (0.95 - 1.05 pu).
- **Warnings**: Highlighted when values stay outside the 0.95-1.05 pu range.

### Loading vs. Voltage (Scatter)
A heatmap showing the relationship between total downstream loading (kWh) and voltage.
- Use this to identify if low voltage is sagging specifically during high load periods.
