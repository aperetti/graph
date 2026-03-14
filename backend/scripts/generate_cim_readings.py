"""
Generate realistic 15-minute interval readings for all real CIM nodes.

Writes one parquet file per month to cim_readings/.
~4876 nodes × 96 intervals/day × 30 days ≈ 14 M rows/month.
We generate 1 month (Jan 2025) at 15-min resolution by default.
~14M rows — chunked monthly for performance.
"""
import duckdb
import sqlite3
import json
import os
import sys
import time
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = SCRIPT_PATH.parents[2]

# Topology lives in SQLite; analytics engine + weather stay in DuckDB.
SQLITE_PATH = os.getenv("TOPOLOGY_DB_PATH", str(WORKSPACE_ROOT / "grid_topology.sqlite"))
DB_PATH = os.getenv("DB_PATH", str(WORKSPACE_ROOT / "grid_data_cim.duckdb"))
PARQUET_DIR = os.getenv("PARQUET_DIR", str(WORKSPACE_ROOT / "cim_readings"))


def _load_topology_into_duckdb(conn, sqlite_path: str):
    """Read topology from SQLite and push into DuckDB temp tables for the
    analytics query which needs DuckDB array functions (list_contains, etc.)."""
    sq = sqlite3.connect(sqlite_path)
    node_rows = sq.execute(
        "SELECT node_id, node_type, phases_present FROM grid_nodes"
    ).fetchall()
    edge_rows = sq.execute(
        "SELECT from_node_id, to_node_id FROM grid_edges"
    ).fetchall()
    sub_rows = sq.execute(
        "SELECT node_id, latitude, longitude FROM grid_nodes WHERE node_type = 'Substation'"
    ).fetchall()
    all_node_ids = sq.execute("SELECT node_id FROM grid_nodes").fetchall()
    sq.close()

    # Create grid_nodes in DuckDB with proper VARCHAR[] array type
    conn.execute("DROP TABLE IF EXISTS grid_nodes")
    conn.execute(
        "CREATE TABLE grid_nodes "
        "(node_id VARCHAR PRIMARY KEY, node_type VARCHAR, phases_present VARCHAR[])"
    )
    parsed = []
    for r in node_rows:
        phases = json.loads(r[2]) if r[2] else ['A', 'B', 'C']
        parsed.append((r[0], r[1], phases))
    conn.executemany("INSERT INTO grid_nodes VALUES (?, ?, ?)", parsed)

    return node_rows, edge_rows, sub_rows, all_node_ids

def main():
    print(f"Using topology DB (SQLite): {SQLITE_PATH}")
    print(f"Using analytics DB (DuckDB): {DB_PATH}")
    print(f"Output parquet dir: {PARQUET_DIR}")

    if not os.path.exists(SQLITE_PATH):
        print(f"ERROR: Cannot find topology DB at {SQLITE_PATH}.", file=sys.stderr)
        print("Tip: run backend/scripts/ingest_cim_graph.py first (or set TOPOLOGY_DB_PATH).", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(PARQUET_DIR):
        print(f"Cleaning existing parquet files in {PARQUET_DIR}...")
        for f in os.listdir(PARQUET_DIR):
            if f.endswith(".parquet"):
                os.remove(os.path.join(PARQUET_DIR, f))
    else:
        os.makedirs(PARQUET_DIR, exist_ok=True)

    print("Loading topology from SQLite into DuckDB analytics engine...")
    with duckdb.connect(DB_PATH) as conn:
        node_rows, edge_rows, sub_rows, all_node_ids = _load_topology_into_duckdb(conn, SQLITE_PATH)

        n = len(node_rows)
        print(f"Found {n} nodes in topology.")
        if n == 0:
            print("ERROR: No nodes found. Run ingest_cim_graph.py first.", file=sys.stderr)
            sys.exit(1)

        # Calculate node distance from closest substation
        print("Calculating node distances from substation...")
        import networkx as nx
        G = nx.Graph()
        G.add_edges_from(edge_rows)

        node_distances = {}
        for sub_row in sub_rows:
            sub_id, sub_lat, sub_lon = sub_row[0], sub_row[1], sub_row[2]
            if sub_id in G:
                root_id = sub_id
            else:
                # Find closest node spatially that IS in the graph
                best_dist = float('inf')
                root_id = None
                for nid in list(G.nodes)[:200]:
                    # simple fallback — pick first reachable node
                    root_id = nid
                    break
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
        for node_row in all_node_ids:
            n_id = node_row[0]
            if n_id not in node_distances:
                dist_rows.append((n_id, float(max_dist), 1.0))

        conn.executemany("INSERT INTO node_distances VALUES (?, ?, ?)", dist_rows)
        print(f"Stored distances for {len(dist_rows)} nodes (max distance = {max_dist}).")

        from datetime import datetime
        now = datetime.now()
        target_end_year = now.year
        target_end_month = now.month + 1 # Reduced from +6 to save CPU/Disk
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
                            MONTH(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS mnth,
                            DAY(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS dy,
                            HOUR(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS hr,
                            DAYOFWEEK(TIMESTAMP '{start_dt}' + (i * INTERVAL '15 minutes')) AS dow
                        FROM range(
                            CAST(0 AS BIGINT),
                            CAST(DATEDIFF('minute', TIMESTAMP '{start_dt}', TIMESTAMP '{end_dt}') / 15 AS BIGINT)
                        ) tbl(i)
                    ),
                    weather_series AS (
                        SELECT t.*, COALESCE(w.temperature, 20.0) as temp
                        FROM time_series t
                        LEFT JOIN weather_recordings w 
                          ON t.mnth = w.month AND t.dy = w.day AND t.hr = w.hour
                    ),
                    combined_load AS (
                        SELECT
                            n.node_id,
                            n.phases_present,
                            n.distance_pct,
                            w.ts AS timestamp,
                            -- Customer Type Intensity based on hash:
                            -- 0-5 (60%): Residential
                            -- 6-8 (30%): Small Commercial
                            -- 9 (10%): Large Commercial (Industrial)
                            CASE 
                                WHEN abs(hash(n.node_id)) % 10 IN (6, 7, 8) THEN 'Commercial'
                                WHEN abs(hash(n.node_id)) % 10 = 9 THEN 'Industrial'
                                ELSE 'Residential'
                            END as cust_type,
                            -- Diurnal Base Load Factor:
                            CASE
                                WHEN abs(hash(n.node_id)) % 10 IN (6, 7, 8, 9) -- Commercial/Industrial
                                    THEN CASE 
                                        WHEN w.hr BETWEEN 8 AND 18 THEN 1.0 
                                        WHEN w.hr BETWEEN 6 AND 22 THEN 0.6
                                        ELSE 0.2 
                                    END
                                ELSE -- Residential
                                    CASE 
                                        WHEN w.hr BETWEEN 6 AND 9 THEN 0.8
                                        WHEN w.hr BETWEEN 17 AND 22 THEN 1.0
                                        WHEN w.hr BETWEEN 9 AND 17 THEN 0.4
                                        ELSE 0.3
                                    END
                            END as base_lf,
                            -- Nocturnal Heating Sensitivity Attenuation:
                            CASE 
                                WHEN w.hr BETWEEN 0 AND 6 THEN 0.4 -- 40% sensitivity at night
                                ELSE 1.0 
                            END as heat_sensitivity,
                            w.temp
                        FROM nodes n
                        CROSS JOIN weather_series w
                    ),
                    final_load AS (
                        SELECT
                            node_id,
                            phases_present,
                            distance_pct,
                            timestamp,
                            (
                                CASE 
                                    WHEN cust_type = 'Commercial' THEN 5.0
                                    WHEN cust_type = 'Industrial' THEN 20.0
                                    ELSE 1.0
                                END
                                * base_lf
                                * (1.0 + (0.15 * heat_sensitivity * GREATEST(0, 18 - temp)) + (0.25 * GREATEST(0, temp - 24)))
                                * (0.7 + 0.6 * random())
                            ) AS lf
                        FROM combined_load
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

                        FROM final_load
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
