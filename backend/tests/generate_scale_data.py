"""Optimized bulk data generation script using DuckDB directly."""
import duckdb
import os
import time

DB_PATH = "grid_data_scale.duckdb"
PARQUET_DIR = "readings_scale"

def init_db():
    conn = duckdb.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS grid_nodes (node_id VARCHAR PRIMARY KEY, node_type VARCHAR, name VARCHAR, phases_present VARCHAR, latitude DOUBLE, longitude DOUBLE);")
    conn.execute("CREATE TABLE IF NOT EXISTS grid_edges (edge_id VARCHAR PRIMARY KEY, from_node_id VARCHAR, to_node_id VARCHAR, conductor_type VARCHAR, phases VARCHAR);")
    if not os.path.exists(PARQUET_DIR):
        os.makedirs(PARQUET_DIR)
    conn.close()

def generate_scale_data(num_meters=100000, days=365):
    """
    Generates data using DuckDB's parallel execution engine directly to Parquet.
    Bypassing Python lists/pandas entirely to avoid OOM for billions of rows.
    """
    print(f"Initializing Database... Target: {num_meters} meters for {days} days.")
    init_db()
    
    start_time = time.time()
    
    with duckdb.connect(DB_PATH) as conn:
        # 1. Generate nodes (Substations, Transformers, Meters)
        print("Generating grid topology...")
        
        # Determine counts based on reasonable distribution
        # 1 Substation per 10,000 meters -> 10 subs
        num_subs = max(1, num_meters // 10000)
        # 1 Transformer per 50 meters -> 2,000 txts
        num_txs = max(1, num_meters // 50)
        
        # Clear existing
        conn.execute("DELETE FROM grid_nodes;")
        conn.execute("DELETE FROM grid_edges;")
        
        # Insert Substations
        conn.execute(f"""
            INSERT INTO grid_nodes (node_id, node_type, name, phases_present, latitude, longitude)
            SELECT 'SUB-' || range, 'SubstationBreaker', 'Substation ' || range, 'ABC',
                   37.7749 + (random() - 0.5) * 0.2, 
                   -122.4194 + (random() - 0.5) * 0.2
            FROM range(1, {num_subs + 1})
        """)
        
        # Insert Transformers
        conn.execute(f"""
            INSERT INTO grid_nodes (node_id, node_type, name, phases_present, latitude, longitude)
            SELECT 'TX-' || range, 'Transformer', 'Transformer ' || range, 
                   CASE WHEN range % 3 = 0 THEN 'A' WHEN range % 3 = 1 THEN 'B' ELSE 'C' END,
                   37.7749 + (random() - 0.5) * 0.2, 
                   -122.4194 + (random() - 0.5) * 0.2
            FROM range(1, {num_txs + 1})
        """)
        
        # Insert Meters
        conn.execute(f"""
            INSERT INTO grid_nodes (node_id, node_type, name, phases_present, latitude, longitude)
            SELECT 'M-' || range, 'Meter', 'Meter ' || range,
                   CASE WHEN range % 3 = 0 THEN 'A' WHEN range % 3 = 1 THEN 'B' ELSE 'C' END,
                   37.7749 + (random() - 0.5) * 0.2, 
                   -122.4194 + (random() - 0.5) * 0.2
            FROM range(1, {num_meters + 1})
        """)
        
        # Create Edges (Substation -> Transformers)
        conn.execute(f"""
            INSERT INTO grid_edges (edge_id, from_node_id, to_node_id, conductor_type, phases)
            SELECT 
                'E-SUB-TX-' || range,
                'SUB-' || ( (range % {num_subs}) + 1),
                'TX-' || range,
                'Overhead',
                CASE WHEN range % 3 = 0 THEN 'A' WHEN range % 3 = 1 THEN 'B' ELSE 'C' END
            FROM range(1, {num_txs + 1})
        """)
        
        # Create Edges (Transformers -> Meters)
        conn.execute(f"""
            INSERT INTO grid_edges (edge_id, from_node_id, to_node_id, conductor_type, phases)
            SELECT 
                'E-TX-M-' || range,
                'TX-' || ( (range % {num_txs}) + 1),
                'M-' || range,
                'ServiceDrop',
                CASE WHEN range % 3 = 0 THEN 'A' WHEN range % 3 = 1 THEN 'B' ELSE 'C' END
            FROM range(1, {num_meters + 1})
        """)
        
        print("Topology generated.")
        
        # 2. Generate Parquet Time-Series Data in Monthly Chunks (36.5 Million rows total)
        print(f"Generating {days} days of 1-day intervals for {num_meters} meters (~36.5 M rows)...")
        
        for month in range(1, 13):
            # Calculate start and end bounds per month roughly
            start_date = f"2025-{month:02d}-01 00:00:00"
            if month == 12:
                end_date = "2026-01-01 00:00:00"
            else:
                end_date = f"2025-{month+1:02d}-01 00:00:00"
                
            print(f"  -> Generating Month {month}/12: {start_date} to {end_date}...")
            
            query = f"""
                COPY (
                    WITH time_series AS (
                        SELECT CAST(generate_series AS TIMESTAMP) as ts
                        FROM generate_series(
                            TIMESTAMP '{start_date}',
                            TIMESTAMP '{end_date}' - INTERVAL 1 DAY,
                            INTERVAL 1 DAY
                        )
                    ),
                    meters AS (
                        SELECT node_id, phases_present FROM grid_nodes WHERE node_type = 'Meter'
                    )
                    SELECT 
                        m.node_id,
                        t.ts as timestamp,
                        0.5 + (random() * 2.0) as kwh_dlv,
                        0.0 as kwh_rcv,
                        CASE WHEN m.phases_present = 'A' THEN 118.0 + (random() * 4) ELSE NULL END as voltage_a,
                        CASE WHEN m.phases_present = 'B' THEN 118.0 + (random() * 4) ELSE NULL END as voltage_b,
                        CASE WHEN m.phases_present = 'C' THEN 118.0 + (random() * 4) ELSE NULL END as voltage_c,
                        CASE WHEN m.phases_present = 'A' THEN 5.0 + (random() * 15) ELSE NULL END as current_a,
                        CASE WHEN m.phases_present = 'B' THEN 5.0 + (random() * 15) ELSE NULL END as current_b,
                        CASE WHEN m.phases_present = 'C' THEN 5.0 + (random() * 15) ELSE NULL END as current_c
                    FROM meters m
                    CROSS JOIN time_series t
                ) TO '{PARQUET_DIR}/readings_2025_{month:02d}.parquet' (FORMAT PARQUET, CODEC 'ZSTD');
            """
            
            chunk_start = time.time()
            conn.execute(query)
            chunk_end = time.time()
            print(f"     Completed Month {month} in {chunk_end - chunk_start:.2f} seconds.")
        
    end_time = time.time()
    print(f"Generation completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    generate_scale_data()
