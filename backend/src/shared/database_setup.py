"""Database Setup and Initialization.

Topology (grid_nodes, grid_edges, alarms) lives in **SQLite** for portability.
DuckDB is kept purely as an analytics engine for parquet / weather queries.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ── SQLite: topology database (grid_nodes, grid_edges, alarms) ────
SQLITE_PATH = os.getenv("TOPOLOGY_DB_PATH", os.path.join(BASE_DIR, "grid_topology.sqlite"))

# ── DuckDB: analytics engine (weather_recordings + parquet reads) ─
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "grid_data_cim.duckdb"))

# ── Parquet directories ───────────────────────────────────────────
PARQUET_DIR = os.getenv("PARQUET_DIR", os.path.join(BASE_DIR, "cim_readings"))
PARQUET_ALARMS_DIR = os.getenv("PARQUET_ALARMS_DIR", os.path.join(BASE_DIR, "cim_alarms"))


def init_db():
    """Initialises the SQLite topology database schema."""
    conn = sqlite3.connect(SQLITE_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS grid_nodes (
            node_id   TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            name      TEXT,
            phases_present TEXT DEFAULT '["A","B","C"]',
            latitude  REAL,
            longitude REAL,
            is_open   INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grid_edges (
            edge_id      TEXT PRIMARY KEY,
            from_node_id TEXT NOT NULL,
            to_node_id   TEXT NOT NULL,
            conductor_type TEXT,
            phases       TEXT DEFAULT '["A","B","C"]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            alarm_id  TEXT PRIMARY KEY,
            node_id   TEXT,
            timestamp TEXT,
            alarm_code TEXT,
            severity  TEXT,
            message   TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()

    os.makedirs(PARQUET_DIR, exist_ok=True)
    os.makedirs(PARQUET_ALARMS_DIR, exist_ok=True)

    print(f"Topology database initialised at {SQLITE_PATH}")


if __name__ == "__main__":
    init_db()
