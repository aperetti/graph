
import duckdb
import pandas as pd

PARQUET_DIR = "cim_readings"

def verify():
    conn = duckdb.connect()
    
    # Check total month count and range
    files = conn.execute(f"SELECT count(*) FROM (SELECT DISTINCT regexp_extract(filename, 'readings_(.*).parquet', 1) as m FROM read_parquet('{PARQUET_DIR}/*.parquet', filename=true))").fetchone()[0]
    print(f"Total months generated: {files}")
    
    # Check seasonal ratios for a few key months
    samples = {
        "Winter (2025-01)": "readings_2025_01.parquet",
        "Summer (2025-07)": "readings_2025_07.parquet",
        "Current (2026-03)": "readings_2026_03.parquet",
        "Future (2026-09)": "readings_2026_09.parquet"
    }
    
    results = []
    for label, file in samples.items():
        path = f"{PARQUET_DIR}/{file}"
        res = conn.execute(f"SELECT avg(kwh_dlv) as avg_kwh FROM read_parquet('{path}')").fetchone()[0]
        results.append({"Label": label, "Avg kWh": res})
        
    df = pd.DataFrame(results)
    print("\n--- 21-Month Seasonal Overview ---")
    print(df.to_string(index=False))
    
    # Check distance scaling (distance_pct effect)
    # distance_pct = distance / max_dist
    # kwh_dlv = base_load * (1 - 0.1 * distance_pct) ... wait, the current logic is:
    # kwh_dlv = load_factor (which has distance_pct?) Let's check the script code.
    
    print("\n--- Distance Scaling Check (Jan 2025) ---")
    # Join with node_distances to verify kwh correlation
    # We'll need the grid_data_cim.duckdb for this
    conn.execute("ATTACH 'grid_data_cim.duckdb' AS cim")
    dist_check = conn.execute(f"""
        SELECT d.distance_pct, avg(r.kwh_dlv) 
        FROM read_parquet('{PARQUET_DIR}/readings_2025_01.parquet') r
        JOIN cim.node_distances d ON r.node_id = d.node_id
        GROUP BY 1 ORDER BY 1 LIMIT 10
    """).fetchall()
    print("Distance Pct | Avg kWh")
    for row in dist_check:
        print(f"{row[0]:.4f} | {row[1]:.4f}")

if __name__ == "__main__":
    verify()
