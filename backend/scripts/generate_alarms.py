"""
Generate synthetic alarms for meters.
Writes active alarms to DuckDB and historical logs to cim_alarms/.
"""
import duckdb
import os
import sys
import uuid
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "..", "grid_data_cim.duckdb"))
PARQUET_ALARMS_DIR = os.getenv("PARQUET_ALARMS_DIR", os.path.join(BASE_DIR, "..", "cim_alarms"))

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Cannot find DB at {DB_PATH}.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(PARQUET_ALARMS_DIR, exist_ok=True)

    print("Connecting to database...")
    with duckdb.connect(DB_PATH) as conn:
        # Get meters and their distances
        meters = conn.execute("""
            SELECT n.node_id, d.distance_pct 
            FROM grid_nodes n 
            JOIN node_distances d ON n.node_id = d.node_id 
            WHERE n.node_type = 'Meter'
        """).fetchall()

        if not meters:
            print("No meters found. Run generate_cim_readings.py first maybe?")
            return

        print(f"Generating alarms for {len(meters)} meters...")
        
        # We'll generate history for Jan 2025 (matching readings)
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 2, 1)
        
        hist_alarms = []
        active_alarms = []
        
        # Alarm types and weights
        alarm_types = [
            ("OV_VOLT", "WARNING"),
            ("UV_VOLT", "CRITICAL"),
            ("PHASE_IMB", "WARNING"),
            ("TAMPER", "CRITICAL"),
            ("COMM_FAIL", "INFO")
        ]

        for node_id, dist_pct in meters:
            # Use hash for deterministic but "random" distribution
            h = abs(hash(node_id))
            
            # Probability of having ANY alarm in a month
            # Let's say 5% baseline, + 10% for far-away nodes (voltage issues)
            prob = 0.05 + (dist_pct * 0.1)
            
            if (h % 1000) / 1000.0 < prob:
                # Generate 1-3 alarms for this node
                num_alarms = (h % 3) + 1
                for i in range(num_alarms):
                    # Pick an alarm type
                    # UV_VOLT is more common for distant nodes
                    if dist_pct > 0.7 and (h + i) % 2 == 0:
                        code, sev = "UV_VOLT", "CRITICAL"
                    else:
                        code, sev = alarm_types[(h + i) % len(alarm_types)]
                    
                    # Random timestamp in Jan 2025
                    ts = start_date + timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                    
                    alarm_id = str(uuid.uuid4())
                    msg = f"Automatic alert: {code} detected at {node_id}"
                    
                    # 10% chance it's still active if it happened in last 2 days of Jan
                    # For this test, let's just make everything after Jan 29 active
                    is_active = ts > datetime(2025, 1, 29)
                    
                    alarm_row = (alarm_id, node_id, ts, code, sev, msg, is_active)
                    hist_alarms.append(alarm_row)
                    if is_active:
                        active_alarms.append(alarm_row)

        print(f"Generated {len(hist_alarms)} historical alarms ({len(active_alarms)} active).")

        # Save active alarms to DuckDB
        print("Saving active alarms to DuckDB...")
        conn.execute("DELETE FROM alarms")
        conn.executemany("INSERT INTO alarms VALUES (?, ?, ?, ?, ?, ?, ?)", active_alarms)

        # Save history to Parquet
        print("Saving history to Parquet...")
        out_file = os.path.join(PARQUET_ALARMS_DIR, "alarms_202501.parquet")
        
        # Convert to temp table to export easily as Parquet via DuckDB
        conn.execute("DROP TABLE IF EXISTS temp_alarms")
        conn.execute("CREATE TABLE temp_alarms (alarm_id VARCHAR, node_id VARCHAR, timestamp TIMESTAMP, alarm_code VARCHAR, severity VARCHAR, message VARCHAR, is_active BOOLEAN)")
        conn.executemany("INSERT INTO temp_alarms VALUES (?, ?, ?, ?, ?, ?, ?)", hist_alarms)
        
        conn.execute(f"COPY temp_alarms TO '{out_file}' (FORMAT PARQUET)")
        conn.execute("DROP TABLE IF EXISTS temp_alarms")
        
        print(f"Alarms dataset generated at {out_file}")

if __name__ == "__main__":
    main()
