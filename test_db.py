import duckdb
conn = duckdb.connect('grid_data_cim.duckdb', read_only=True)
nodes_db = conn.execute("SELECT node_id FROM grid_nodes LIMIT 1").fetchall()
nodes_pq = conn.execute("SELECT node_id FROM read_parquet('cim_readings/*.parquet') LIMIT 1").fetchall()
print("DB node_id:", repr(nodes_db[0][0]))
print("PQ node_id:", repr(nodes_pq[0][0]))
