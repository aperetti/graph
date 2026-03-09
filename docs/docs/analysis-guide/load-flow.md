# Phase Balancing (Load Flow)

Phase Balancing analysis allows engineers to identify "unbalanced" transformers or circuits where one phase is heavily loaded while others are under-utilized.

## Why it matters
Unbalanced loads cause neutral currents, excessive heat in transformers, and increased system losses.

## Running the Analysis

1. Right-click a **Substation** or **Transformer**.
2. Select **Run Phase Balance**.
3. Choose your temporal granularity.

## Key Metrics

- **Total kWh Delivered**: The aggregate energy consumption downstream during the period.
- **Median Current (Amps)**: The typical loading on Phase A, B, and C.
- **Imbalance Delta**: The difference between the highest and lowest loaded phase.
- **Peak Loading Time**: Identifies *when* the system was most stressed.

## Remediation
If the **Imbalance Delta** is high, consider re-tapping single-phase meters or lateral lines to a different primary phase.
