"""
Generate realistic 15-minute interval readings for all real CIM nodes.

Writes one parquet file per month to cim_readings/.
~4876 nodes × 96 intervals/day × 365 days ≈ 170 M rows/year (heavy).
We generate 6 months (Jan-Jun 2025) at 15-min resolution which is
~85M rows — chunked monthly so DuckDB streams it without OOM.
"""
import duckdb
import os
import sys
import time

# Adjusted paths — run from repo root (c:/Users/adamp/Development/graph)
DB_PATH = os.getenv("DB_PATH", "grid_data_cim.duckdb")
PARQUET_DIR = os.getenv("PARQUET_DIR", "cim_readings")

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Cannot find DB at {DB_PATH}. Run from repo root.", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(PARQUET_DIR):
        print(f"Cleaning existing parquet files in {PARQUET_DIR}...")
        for f in os.listdir(PARQUET_DIR):
            if f.endswith(".parquet"):
                os.remove(os.path.join(PARQUET_DIR, f))
    else:
        os.makedirs(PARQUET_DIR, exist_ok=True)

    print("Connecting to CIM database...")
    with duckdb.connect(DB_PATH) as conn:
        # Verify node count
        n = conn.execute("SELECT COUNT(*) FROM grid_nodes").fetchone()[0]
        print(f"Found {n} nodes in grid_nodes.")

        # Calculate node distance from closest substation
        print("Calculating node distances from substation...")
        edges = conn.execute("SELECT from_node_id, to_node_id FROM grid_edges").fetchall()
        subs = conn.execute("SELECT node_id FROM grid_nodes WHERE node_type = 'Substation'").fetchall()
        
        import networkx as nx
        G = nx.Graph()
        G.add_edges_from(edges)
        
        node_distances = {}
        for sub in subs:
            sub_id = sub[0]
            if sub_id in G:
                root_id = sub_id
            else:
                # Find closest node spatially that IS in the graph
                sub_lat, sub_lon = conn.execute(f"SELECT latitude, longitude FROM grid_nodes WHERE node_id = '{sub_id}'").fetchone()
                nearby = conn.execute(f"""
                    SELECT node_id FROM grid_nodes 
                    ORDER BY (latitude - {sub_lat})*(latitude - {sub_lat}) + (longitude - {sub_lon})*(longitude - {sub_lon}) ASC
                    LIMIT 200
                """).fetchall()
                root_id = next((nid[0] for nid in nearby if nid[0] in G), None)
                if root_id:
                    print(f"Substation disconnected. Using spatial root {root_id} for {sub_id}")
            
            if root_id:
                lengths = nx.single_source_shortest_path_length(G, root_id)
                for node, dist in lengths.items():
                    if node not in node_distances or dist < node_distances[node]:
                        node_distances[node] = dist
                        
        max_dist = max(node_distances.values()) if node_distances else 1
        
        conn.execute("DROP TABLE IF EXISTS node_distances")
        conn.execute("CREATE TABLE node_distances (node_id VARCHAR, distance DOUBLE, distance_pct DOUBLE)")
        dist_rows = [(n_id, float(d), float(d)/max_dist) for n_id, d in node_distances.items()]
        
        # Some Isolated nodes might not be in G, give them max_dist
        all_nodes = conn.execute("SELECT node_id FROM grid_nodes").fetchall()
        for node_row in all_nodes:
            n_id = node_row[0]
            if n_id not in node_distances:
                dist_rows.append((n_id, float(max_dist), 1.0))

        conn.executemany("INSERT INTO node_distances VALUES (?, ?, ?)", dist_rows)
        print(f"Stored distances for {len(dist_rows)} nodes (max distance = {max_dist}).")

        from datetime import datetime
        now = datetime.now()
        target_end_year = now.year
        target_end_month = now.month + 6
        if target_end_month > 12:
            target_end_year += (target_end_month - 1) // 12
            target_end_month = (target_end_month - 1) % 12 + 1

        months = []
        curr_year, curr_month = 2025, 1
        while (curr_year < target_end_year) or (curr_year == target_end_year and curr_month <= target_end_month):
            start_dt = f"{curr_year}-{curr_month:02d}-01"
            
            next_month = curr_month + 1
            next_year = curr_year
            if next_month > 12:
                next_month = 1
                next_year += 1
            
            end_dt = f"{next_year}-{next_month:02d}-01"
            months.append((start_dt, end_dt))
            
            curr_year, curr_month = next_year, next_month

        total_start = time.time()

        for idx, (start_dt, end_dt) in enumerate(months, 1):
            month_label = start_dt[:7]
            out_file = f"{PARQUET_DIR}/readings_{month_label.replace('-', '_')}.parquet"

            if os.path.exists(out_file):
                print(f"  -> Month {idx}/12 ({month_label}): already exists, skipping.")
                continue

            print(f"  -> Month {idx}/{len(months)} ({month_label}): generating...")
            chunk_start = time.time()

            # Use range(0, N) intervals from epoch to avoid DuckDB generate_series STRUCT issue
            query = f"""
                COPY (
                    WITH
                    nodes AS (
                        SELECT n.node_id, n.phases_present, COALESCE(d.distance_pct, 1.0) as distance_pct
                        FROM grid_nodes n
                        LEFT JOIN node_distances d ON n.node_id = d.node_id
                    ),
                    time_series AS (
                        SELECT
                            TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes') AS ts,
                            HOUR(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS hr,
                            MONTH(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS mnth,
                            DAYOFWEEK(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS dow
                        FROM range(
                            CAST(0 AS BIGINT),
                            CAST(DATEDIFF('minute', TIMESTAMP '{start_dt}', TIMESTAMP '{end_dt}') / 15 AS BIGINT)
                        ) tbl(i)
                    ),
                    combined_load AS (
                        SELECT
                            n.node_id,
                            n.phases_present,
                            n.distance_pct,
                            t.ts AS timestamp,
                            -- Customer Type Intensity based on hash:
                            -- 0-5 (60%): Residential (1x base)
                            -- 6-8 (30%): Small Commercial (5x base)
                            -- 9 (10%): Large Commercial (20x base)
                            CASE 
                                WHEN abs(hash(n.node_id)) % 10 IN (6, 7, 8) THEN 5.0
                                WHEN abs(hash(n.node_id)) % 10 = 9 THEN 20.0
                                ELSE 1.0
                            END
                            -- Hour-of-day seasonal profiles:
                            -- User wants Peak Ratios: Winter 1.0, Summer 0.8, Fall 0.4, Spring 0.3
                            -- Winter profile base peak is ~0.6. Normalizing multipliers to this peak.
                            * CASE 
                                WHEN t.mnth IN (12, 1, 2) THEN -- Winter: 2 peaks, normalized to 1.0 ratio
                                    (0.15 + 0.40 * EXP(-POW(t.hr - 7, 2) / 8.0) + 0.45 * EXP(-POW(t.hr - 19, 2) / 12.0)) * 1.66
                                WHEN t.mnth IN (6, 7, 8) THEN -- Summer: Peak ratio 0.8 (0.8 / 1.0 relative to winter)
                                    (0.25 + 0.75 * EXP(-POW(t.hr - 16, 2) / 15.0)) * 0.80
                                WHEN t.mnth IN (3, 4, 5) THEN -- Spring: Peak ratio 0.3
                                    (0.40 + 0.30 * EXP(-POW(t.hr - 18, 2) / 20.0)) * 0.43
                                ELSE -- Fall: Peak ratio 0.4
                                    (0.40 + 0.40 * EXP(-POW(t.hr - 18, 2) / 20.0)) * 0.50
                            END
                            -- Per-node variability factor
                            * (0.7 + 0.6 * random())
                            -- Weekend drop (dow 0=Sun, 6=Sat)
                            * (CASE WHEN t.dow IN (0, 6) THEN 0.75 ELSE 1.0 END)
                            -- Correlated daily weather offset
                            * (0.9 + 0.2 * (ABS(hash(CAST(t.ts AS DATE))) % 1000) / 1000.0)
                            -- Correlated interval jitter
                            * (0.95 + 0.1 * (ABS(hash(t.ts)) % 1000) / 1000.0) AS lf
                        FROM nodes n
                        CROSS JOIN time_series t
                    ),
                    -- kWh and Voltages derived from load factor
                    combined AS (
                        SELECT
                            node_id,
                            timestamp,

                            -- kWh delivered: proportional to load factor
                            ROUND(0.20 * lf, 6) AS kwh_dlv,

                            -- Voltages per phase (122V-124V nominal at sub, drops 0-5% based on load, 0-5% based on distance)
                            CASE WHEN list_contains(phases_present, 'A')
                                THEN ROUND((123.0 + (random() - 0.5) * 2.0) * (1.0 - LEAST(lf / 8.0, 1.0) * 0.05 - distance_pct * 0.05), 3) END AS voltage_a,
                            CASE WHEN list_contains(phases_present, 'B')
                                THEN ROUND((123.0 + (random() - 0.5) * 2.0) * (1.0 - LEAST(lf / 8.0, 1.0) * 0.05 - distance_pct * 0.05), 3) END AS voltage_b,
                            CASE WHEN list_contains(phases_present, 'C')
                                THEN ROUND((123.0 + (random() - 0.5) * 2.0) * (1.0 - LEAST(lf / 8.0, 1.0) * 0.05 - distance_pct * 0.05), 3) END AS voltage_c,

                            -- Currents per phase (proportional to load)
                            CASE WHEN list_contains(phases_present, 'A')
                                THEN ROUND(2.0 + lf * 25.0, 3) END AS current_a,
                            CASE WHEN list_contains(phases_present, 'B')
                                THEN ROUND(2.0 + lf * 25.0, 3) END AS current_b,
                            CASE WHEN list_contains(phases_present, 'C')
                                THEN ROUND(2.0 + lf * 25.0, 3) END AS current_c

                        FROM combined_load
                    )
                    SELECT * FROM combined
                    ORDER BY node_id, timestamp
                ) TO '{out_file}' (FORMAT PARQUET, CODEC 'ZSTD', ROW_GROUP_SIZE 100000);
            """

            conn.execute(query)
            elapsed = time.time() - chunk_start
            size_mb = os.path.getsize(out_file) / 1_048_576
            print(f"     Done in {elapsed:.1f}s — {size_mb:.1f} MB written to {out_file}")

        total_elapsed = time.time() - total_start
        print(f"\nAll months complete in {total_elapsed:.1f}s")

        # Quick sanity check
        row_count = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{PARQUET_DIR}/*.parquet')").fetchone()[0]
        date_range = conn.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM read_parquet('{PARQUET_DIR}/*.parquet')").fetchone()
        print(f"Total rows in parquet: {row_count:,}")
        print(f"Date range: {date_range[0]} → {date_range[1]}")

if __name__ == "__main__":
    main()
