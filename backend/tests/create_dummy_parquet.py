import duckdb
import os

PARQUET_DIR = os.getenv("PARQUET_DIR", "cim_readings")
if not os.path.exists(PARQUET_DIR):
    os.makedirs(PARQUET_DIR)

conn = duckdb.connect()
conn.execute(f"""
    COPY (
        SELECT
            'NODE1' as node_id,
            CAST('2023-01-01 12:00:00' AS TIMESTAMP) as timestamp,
            10.0 as kwh_dlv,
            5.0 as current_a,
            5.0 as current_b,
            5.0 as current_c,
            120.0 as voltage_a,
            120.0 as voltage_b,
            120.0 as voltage_c
    ) TO '{PARQUET_DIR}/dummy.parquet' (FORMAT PARQUET);
""")
# Also need weather recordings table to avoid join error if it exists...
# wait, the JOIN is on weather_recordings. Let's create it in DuckDB.
db_path = os.getenv("DB_PATH", "grid_data_cim.duckdb")
db_conn = duckdb.connect(db_path)
db_conn.execute("""
    CREATE TABLE IF NOT EXISTS weather_recordings (
        month INT,
        day INT,
        hour INT,
        temperature DOUBLE
    );
    INSERT INTO weather_recordings VALUES (1, 1, 12, 70.0);
""")
