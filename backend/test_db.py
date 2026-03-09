from src.shared.graph_engine import GraphEngine

g = GraphEngine('grid_data_cim.duckdb')
# Try a known node id, or maybe a substation node
import duckdb
conn = duckdb.connect('grid_data_cim.duckdb', read_only=True)
edge = conn.execute("SELECT source_id, target_id FROM edges LIMIT 1").fetchone()
print("Test edge:", edge)

downstream = g.find_downstream(edge[0])
print("Downstream nodes count:", len(downstream))
if len(downstream) > 0:
    print("Sample:", downstream[:5])
else:
    print("NO DOWNSTREAM NODES FOUND FOR:", edge[0])
