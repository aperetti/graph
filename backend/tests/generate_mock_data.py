"""Mock data generation script for testing."""
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import random
from datetime import datetime, timedelta
from src.shared.database_setup import init_db, DB_PATH, PARQUET_DIR

def generate_mock_data():
    """Generates a sample micro-grid and corresponding time-series data."""
    print("Initializing Database...")
    init_db()
    
    with duckdb.connect(DB_PATH) as conn:
        print("Inserting graph nodes...")
        import random
        base_lat = 37.7749 # San Francisco
        base_lon = -122.4194

        def random_offset():
            return (random.random() - 0.5) * 0.01

        # Insert Mock Nodes
        print("Inserting nodes...")
        conn.execute("INSERT INTO grid_nodes VALUES ('SUB-1', 'SubstationBreaker', 'Main Substation', 'ABC', ?, ?) ON CONFLICT DO NOTHING", (base_lat, base_lon))
        conn.execute("INSERT INTO grid_nodes VALUES ('TX-A', 'Transformer', 'Transformer A', 'A', ?, ?) ON CONFLICT DO NOTHING", (base_lat + random_offset(), base_lon + random_offset()))
        conn.execute("INSERT INTO grid_nodes VALUES ('TX-B', 'Transformer', 'Transformer B', 'B', ?, ?) ON CONFLICT DO NOTHING", (base_lat + random_offset(), base_lon + random_offset()))
        
        conn.execute("INSERT INTO grid_nodes VALUES ('M-1', 'Meter', 'Meter 1', 'A', ?, ?) ON CONFLICT DO NOTHING", (base_lat + random_offset(), base_lon + random_offset()))
        conn.execute("INSERT INTO grid_nodes VALUES ('M-2', 'Meter', 'Meter 2', 'A', ?, ?) ON CONFLICT DO NOTHING", (base_lat + random_offset(), base_lon + random_offset()))
        conn.execute("INSERT INTO grid_nodes VALUES ('M-3', 'Meter', 'Meter 3', 'B', ?, ?) ON CONFLICT DO NOTHING", (base_lat + random_offset(), base_lon + random_offset()))
        conn.execute("INSERT INTO grid_nodes VALUES ('M-4', 'Meter', 'Meter 4', 'B', ?, ?) ON CONFLICT DO NOTHING", (base_lat + random_offset(), base_lon + random_offset()))
        
        print("Inserting graph edges...")
        edges = [
            ("E-1", "SUB-1", "TX-A", "Overhead", "AB"),
            ("E-2", "SUB-1", "TX-B", "Underground", "C"),
            ("E-3", "TX-A", "M-1", "ServiceDrop", "A"),
            ("E-4", "TX-A", "M-2", "ServiceDrop", "B"),
            ("E-5", "TX-B", "M-3", "ServiceDrop", "C"),
            ("E-6", "TX-B", "M-4", "ServiceDrop", "C"),
        ]
        conn.executemany("INSERT INTO grid_edges VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING", edges)
        
    print("Generating Time Series Parquet data...")
    meter_ids = ["M-1", "M-2", "M-3", "M-4"]
    rows = []
    
    # Generate 1 hour of 15-minute intervals for today
    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for meter_id in meter_ids:
        # Determine active phase for this meter
        phase = 'A' if meter_id == 'M-1' else ('B' if meter_id == 'M-2' else 'C')
        
        for i in range(4): # 4 intervals
            ts = start_time + timedelta(minutes=15 * i)
            base_v = 119.5 + random.uniform(-2, 2)
            base_i = random.uniform(5, 20)
            
            row = {
                "node_id": meter_id,
                "timestamp": ts,
                "kwh_dlv": random.uniform(0.1, 1.5),
                "kwh_rcv": 0.0,
                "voltage_a": base_v if phase == 'A' else None,
                "voltage_b": base_v if phase == 'B' else None,
                "voltage_c": base_v if phase == 'C' else None,
                "current_a": base_i if phase == 'A' else None,
                "current_b": base_i if phase == 'B' else None,
                "current_c": base_i if phase == 'C' else None,
            }
            rows.append(row)
            
    df = pd.DataFrame(rows)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, f"{PARQUET_DIR}/readings_mock.parquet")
    print(f"Wrote {len(rows)} records to {PARQUET_DIR}/readings_mock.parquet")

if __name__ == "__main__":
    generate_mock_data()
