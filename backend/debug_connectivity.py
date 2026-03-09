
import duckdb
import networkx as nx

DB_PATH = "grid_data_cim.duckdb"

def debug():
    with duckdb.connect(DB_PATH) as conn:
        print("--- Node Types ---")
        res = conn.execute("SELECT node_type, count(*) FROM grid_nodes GROUP BY 1").fetchall()
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        print("\n--- Substation IDs ---")
        subs = conn.execute("SELECT node_id FROM grid_nodes WHERE node_type = 'Substation'").fetchall()
        sub_list = [s[0] for s in subs]
        print(f"Substations found: {len(sub_list)}")
        
        print("\n--- Graph Check ---")
        all_edges = conn.execute("SELECT from_node_id, to_node_id FROM grid_edges").fetchall()
        G = nx.Graph()
        G.add_edges_from(all_edges)
        print(f"Graph nodes: {G.number_of_nodes()}")
        print(f"Graph edges: {G.number_of_edges()}")
        
        if sub_list:
            sub_id = sub_list[0]
            if sub_id in G:
                lengths = nx.single_source_shortest_path_length(G, sub_id)
                print(f"Nodes reachable from sub {sub_id}: {len(lengths)}")
                if len(lengths) > 1:
                    max_d = max(lengths.values())
                    print(f"Max distance from this sub: {max_d}")
            else:
                print(f"Substation {sub_id} NOT found in graph nodes (edges table)!")
                # Find nodes with degree 1 or nodes that seem like roots
                roots = [n for n, d in G.degree() if d == 1]
                print(f"Found {len(roots)} nodes with degree 1. Sample: {roots[:5]}")
                
                # Check for other substation-like node types
                sub_breakers = conn.execute("SELECT node_id FROM grid_nodes WHERE node_type LIKE 'Substation%'").fetchall()
                print(f"Other potential sub nodes: {len(sub_breakers)}")
                
                # Find connected components
                components = list(nx.connected_components(G))
                print(f"Number of connected components: {len(components)}")
                for i, c in enumerate(components[:3]):
                    print(f"Component {i} size: {len(c)}")
                    # Find a node in this component that is in grid_nodes but not in edges?
                    # No, all nodes in edges are in G.
                    # Let's find nodes in this component and check their type.
                    sample_node = list(c)[0]
                    ntype = conn.execute(f"SELECT node_type FROM grid_nodes WHERE node_id = '{sample_node}'").fetchone()
                    print(f"  Sample node {sample_node} type: {ntype[0] if ntype else 'Unknown'}")

if __name__ == "__main__":
    debug()
