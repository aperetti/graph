import duckdb
conn = duckdb.connect("c:/Users/adamp/Development/graph/grid_data_cim.duckdb", read_only=True)
schema = conn.execute("DESCRIBE SELECT * FROM read_parquet('c:/Users/adamp/Development/graph/cim_readings/*.parquet') LIMIT 1").fetchall()
for col in schema:
    print(f"  {col[0]:20s} {col[1]}")
conn.close()
