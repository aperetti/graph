"""DuckDB Database Setup and Initialization."""
import duckdb
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "grid_data_cim.duckdb"))
PARQUET_DIR = os.getenv("PARQUET_DIR", os.path.join(BASE_DIR, "cim_readings"))

def init_db():
    """Initializes the DuckDB database schema."""
    conn = duckdb.connect(DB_PATH)
    
    # Create the grid_nodes table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grid_nodes (
            node_id VARCHAR PRIMARY KEY,
            node_type VARCHAR,
            name VARCHAR,
            phases_present VARCHAR,
            latitude DOUBLE, is_open BOOLEAN,
            longitude DOUBLE
        );
    """)
    
    # Create the grid_edges table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grid_edges (
            edge_id VARCHAR PRIMARY KEY,
            from_node_id VARCHAR,
            to_node_id VARCHAR,
            conductor_type VARCHAR,
            phases VARCHAR
        );
    """)
    
    # Create directory for Parquet files if it doesn't exist
    if not os.path.exists(PARQUET_DIR):
        os.makedirs(PARQUET_DIR)
        
    print(f"Database initialized at {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    init_db()
