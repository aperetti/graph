from src.grid.networkx_engine import NetworkXEngine
from src.shared.duckdb_repository import DuckDBRepository

repo = DuckDBRepository('grid_data_cim.duckdb')
edges = repo.get_all_edges()

engine = NetworkXEngine()
engine.build_graph(edges=edges)

# pick a random edge to test
if len(edges) > 0:
    test_node = edges[0]["from_node_id"]
    downstream = engine.find_downstream(test_node)
    print(f"Node {test_node} is in graph? {test_node in engine.graph}")
    print(f"Downstream count: {len(downstream)}")
else:
    print("NO EDGES IN DB")
