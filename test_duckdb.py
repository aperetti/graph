import duckdb

conn = duckdb.connect("grid_data_cim.duckdb", read_only=True)
query = """
SELECT 
    timestamp,
    
    -- Phase A
    MIN(voltage_a) as min_a,
    approx_quantile(voltage_a, 0.25) as p25_a,
    MEDIAN(voltage_a) as median_a,
    approx_quantile(voltage_a, 0.75) as p75_a,
    MAX(voltage_a) as max_a
FROM read_parquet('readings/*.parquet')
WHERE node_id IN ('3FE0C37D-1892-4EAF-8518-7FA762527D01') 
    AND timestamp >= '2026-02-27T04:37:38' 
    AND timestamp <= '2026-03-06T04:37:38'
GROUP BY timestamp
ORDER BY timestamp ASC
"""

try:
    print(conn.execute(query).fetchall())
except Exception as e:
    print("ERROR:", e)
