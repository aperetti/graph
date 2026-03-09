"""Use Case: Trace Upstream."""
from src.shared.graph_engine import GraphEngine

class TraceUpstreamUseCase:
    """Finds all devices/assets physically upstream to the source (e.g., Substation Breaker)."""
    
    def __init__(self, graph_engine: GraphEngine):
        self.graph_engine = graph_engine
        
    def execute(self, start_node_id: str):
        """Executes the upstream trace."""
        return self.graph_engine.find_upstream(start_node_id)
