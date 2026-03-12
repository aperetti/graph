"""Use Case: Get Active Alarms."""
from typing import List, Optional
from src.shared.repository import AssetRepository
from src.shared.graph_engine import GraphEngine
from src.grid.alarm import Alarm

class GetActiveAlarmsUseCase:
    """Retrieves active alarms for a node or its downstream assets."""
    
    def __init__(self, repository: AssetRepository, graph_engine: GraphEngine):
        self.repository = repository
        self.graph_engine = graph_engine
        
    def execute(self, node_id: str, include_downstream: bool = True) -> List[Alarm]:
        """
        Executes the alarm retrieval.
        If include_downstream is True, it finds all downstream node IDs 
        and fetches active alarms for any of those nodes.
        """
        target_node_ids = [node_id]
        
        if include_downstream:
            # Find all downstream nodes
            downstream_ids = self.graph_engine.find_downstream(node_id)
            target_node_ids.extend(downstream_ids)
            
        # Deduplicate
        target_node_ids = list(set(target_node_ids))
        
        # In a real high-scale system, we'd have a repository method that takes a list of IDs.
        # For now, we'll fetch all active alarms and filter in memory, 
        # or add a better method to DuckDBRepository if needed.
        # Actually, let's just fetch all active alarms for the target IDs.
        
        all_active = self.repository.get_active_alarms()
        return [a for a in all_active if a.node_id in target_node_ids]
