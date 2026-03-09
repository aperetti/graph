
import duckdb
import networkx as nx

DB_PATH = "grid_data_cim.duckdb"

def find_spatial_root():
    with duckdb.connect(DB_PATH) as conn:
        subs = conn.execute("SELECT node_id, latitude, longitude FROM grid_nodes WHERE node_type = 'Substation'").fetchall()
        if not subs:
            print("No substation found in grid_nodes!")
            return
            
        sub_id, sub_lat, sub_lon = subs[0]
        print(f"Substation: {sub_id} at ({sub_lat}, {sub_lon})")
        
        edges = conn.execute("SELECT from_node_id, to_node_id FROM grid_edges").fetchall()
        G = nx.Graph()
        G.add_edges_from(edges)
        
        if sub_id in G:
            print("Substation is in the graph!")
            root_id = sub_id
        else:
            print("Substation NOT in graph. Finding closest node spatially...")
            
            # Find nodes near the sub that are in G
            nearby = conn.execute(f"""
                SELECT node_id, 
                       (latitude - {sub_lat})*(latitude - {sub_lat}) + 
                       (longitude - {sub_lon})*(longitude - {sub_lon}) as dist_sq
                FROM grid_nodes
                ORDER BY dist_sq ASC
                LIMIT 500
            """).fetchall()
            
            root_id = None
            for nid, dist_sq in nearby:
                if nid in G:
                    root_id = nid
                    print(f"Found spatial root: {root_id} at dist_sq {dist_sq}")
                    break
            
            if not root_id:
                print("Could not find any nearby node in the graph!")
                return
        
        lengths = nx.single_source_shortest_path_length(G, root_id)
        print(f"Reachable nodes: {len(lengths)}")
        print(f"Max distance: {max(lengths.values())}")

if __name__ == "__main__":
    find_spatial_root()
