import sys
import duckdb

db_path = r"c:\Users\adamp\Development\graph\grid_data_cim.duckdb"
parquet_dir = r"c:\Users\adamp\Development\graph\cim_readings"

try:
    with duckdb.connect(db_path, read_only=True) as conn:
        res = conn.execute("SELECT node_id FROM grid_nodes WHERE node_type='Meter' LIMIT 5").fetchall()
        node_ids = [r[0] for r in res]
        nodes_list = "'" + "','".join(node_ids) + "'"

        start_time = '2025-01-01T00:00:00'
        end_time = '2026-01-01T00:00:00'

        heatmap_query = f"""
            WITH total_loading AS (
                SELECT timestamp, SUM(kwh_dlv) as total_kwh
                FROM read_parquet('{parquet_dir}/*.parquet')
                WHERE node_id IN ({nodes_list})
                  AND timestamp >= '{start_time}'
                  AND timestamp <= '{end_time}'
                GROUP BY timestamp
            )
            SELECT 
                t.total_kwh as loading,
                r.voltage_a as voltage,
                CAST(COUNT(*) AS INTEGER) as cnt
            FROM read_parquet('{parquet_dir}/*.parquet') r
            JOIN total_loading t ON r.timestamp = t.timestamp
            WHERE r.node_id IN ({nodes_list})
              AND r.timestamp >= '{start_time}' 
              AND r.timestamp <= '{end_time}'
              AND r.voltage_a IS NOT NULL
              AND t.total_kwh IS NOT NULL
            GROUP BY 1, 2
        """

        print("Testing reservoir...")
        try:
            heat_results = conn.execute(f"SELECT * FROM ({heatmap_query}) USING SAMPLE reservoir(10000)").fetchall()
            print("Heatmap rows (reservoir):", len(heat_results))
        except Exception as ex:
            print("Reservoir query failed:", ex)
            
except Exception as e:
    print("Error:", e)
