import duckdb
conn = duckdb.connect(':memory:')
conn.execute('CREATE TABLE test (timestamp VARCHAR, node_id VARCHAR, voltage_a FLOAT)')
conn.execute("INSERT INTO test VALUES ('2023-01-01', 'node1', 120.0), ('2023-01-02', 'node2', 121.0)")

query = """
    SELECT node_id, AVG(voltage_a) as v
    FROM test
    WHERE timestamp >= ?
      AND timestamp <= ?
      AND voltage_a IS NOT NULL
      AND node_id IN (?, ?)
    GROUP BY node_id
"""
print(conn.execute(query, ['2023-01-01', '2023-01-03', 'node1', 'node2']).fetchall())
