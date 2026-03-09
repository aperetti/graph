"""Use Case: Discover Downstream."""
from src.shared.graph_engine import GraphEngine

class DiscoverDownstreamUseCase:
    """Finds all devices/assets physically downstream from a given node."""
    
    def __init__(self, graph_engine: GraphEngine):
        self.graph_engine = graph_engine
        
    def execute(self, start_node_id: str):
        """Executes the downstream discovery."""
        return self.graph_engine.find_downstream(start_node_id)
