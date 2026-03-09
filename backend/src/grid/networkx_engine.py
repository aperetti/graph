"""NetworkX Graph Engine Implementation."""
import networkx as nx
from typing import List
from src.shared.graph_engine import GraphEngine
from src.grid.graph_node import GraphNode

class NetworkXEngine(GraphEngine):
    """Graph engine implementation using NetworkX."""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.nodes = {} # id -> GraphNode
        self.pos_to_nodes = {} # (lat, lon) -> list of node_ids
        
    def build_graph(self, nodes: List[GraphNode] = None, edges: List[dict] = None) -> None:
        """Constructs the directed graph with spatial stitching for coincident nodes."""
        self.graph.clear()
        self.nodes = {}
        self.pos_to_nodes = {}
        
        # 1. Register all nodes and build spatial index
        if nodes:
            for node in nodes:
                self.nodes[node.id] = node
                if node.latitude is not None and node.longitude is not None:
                    pos = (round(node.latitude, 8), round(node.longitude, 8))
                    if pos not in self.pos_to_nodes:
                        self.pos_to_nodes[pos] = []
                    self.pos_to_nodes[pos].append(node.id)
                    
        # 2. Add edges
        if edges:
            for edge in edges:
                self.graph.add_edge(
                    edge["from_node_id"], 
                    edge["to_node_id"], 
                    edge_id=edge["edge_id"],
                    phases=edge.get("phases", ["A", "B", "C"])
                )
                
        # 3. Perform Spatial Stitching
        # Add virtual edges between nodes at the same physical location
        for pos, node_ids in self.pos_to_nodes.items():
            if len(node_ids) > 1:
                for i in range(len(node_ids)):
                    for j in range(i + 1, len(node_ids)):
                        u, v = node_ids[i], node_ids[j]
                        # Add bidirectional virtual "stitch" edges
                        # We use a special prefix so they doesn't get confused with real edges
                        self.graph.add_edge(u, v, edge_id=f"stitch_{u}_{v}", virtual=True)
                        self.graph.add_edge(v, u, edge_id=f"stitch_{v}_{u}", virtual=True)

    def find_downstream(self, start_node_id: str, max_depth: int = None) -> tuple[List[str], List[str]]:
        """Finds all node IDs and edge IDs logically downstream.
        Traverses the directed graph in the forward direction."""
        if start_node_id not in self.graph:
            return [], []
            
        return self._bfs_traversal(self.graph, start_node_id, max_depth)

    def find_upstream(self, start_node_id: str, max_depth: int = None) -> tuple[List[str], List[str]]:
        """Finds all node IDs and edge IDs logically upstream.
        Traverses the directed graph in the reverse direction."""
        if start_node_id not in self.graph:
            return [], []
            
        # Reverse graph to follow flow "upwards"
        reversed_graph = self.graph.reverse()
        return self._bfs_traversal(reversed_graph, start_node_id, max_depth)

    def _bfs_traversal(self, graph: nx.Graph | nx.DiGraph | nx.MultiDiGraph, start_node_id: str, max_depth: int = None) -> tuple[List[str], List[str]]:
        """Generic BFS traversal for finding nodes and edges."""
        nodes = set()
        edges = set()
        
        queue = [(start_node_id, 0)]
        visited_nodes = {start_node_id}
        
        while queue:
            current_node, depth = queue.pop(0)
            if max_depth is not None and depth >= max_depth:
                continue
                
            # For DiGraph and MultiDiGraph, edges(node) returns all outgoing edges
            # This handles both branched paths and parallel edges between same nodes
            if hasattr(graph, 'edges'):
                for _, neighbor, data in graph.edges(current_node, data=True):
                    # Capture real edge IDs (ignore virtual stitch edges for the result)
                    if "edge_id" in data and not data.get("virtual", False):
                        edges.add(data["edge_id"])
                        
                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        nodes.add(neighbor)
                        queue.append((neighbor, depth + 1))
            else:
                # Fallback for undirected regular Graph if needed
                for neighbor in graph.neighbors(current_node):
                    edge_data = graph.get_edge_data(current_node, neighbor)
                    if edge_data and "edge_id" in edge_data:
                        edges.add(edge_data["edge_id"])
                    
                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        nodes.add(neighbor)
                        queue.append((neighbor, depth + 1))
                        
        return list(nodes), list(edges)
