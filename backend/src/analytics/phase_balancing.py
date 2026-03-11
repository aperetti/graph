"""Use Case: Phase Balancing Analytics."""
from overrides import overrides
import duckdb
from typing import Dict, Any
from src.shared.graph_engine import GraphEngine

class PhaseBalancingUseCase:
    """Aggregates energy or current across phases to identify imbalances."""
    
    def __init__(self, graph_engine: GraphEngine, db_path: str, parquet_dir: str = 'readings'):
        self.graph_engine = graph_engine
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        
    def execute(self, start_node_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """
        Executes the phase balancing query for downstream meters.
        
        Args:
            start_node_id: The asset to evaluate imbalance for.
            start_time: ISO timestamp string.
            end_time: ISO timestamp string.
            
        Returns:
            Dictionary with phase aggregations.
        """
        downstream_nodes, downstream_edges = self.graph_engine.find_downstream(start_node_id)
        
        # If no downstream (leaf node like a Meter), query the node itself
        nodes_to_query = downstream_nodes if downstream_nodes else [start_node_id]
             
        # Use placeholders for parameterized query
        placeholders = ",".join(["?"] * len(nodes_to_query))
        
        query = f"""
            SELECT 
                timestamp,
                SUM(COALESCE(current_a, 0)) as current_a,
                SUM(COALESCE(current_b, 0)) as current_b,
                SUM(COALESCE(current_c, 0)) as current_c,
                SUM(COALESCE(kwh_dlv, 0)) as kwh
            FROM read_parquet('{self.parquet_dir}/*.parquet')
            WHERE node_id IN ({placeholders})
              AND timestamp >= ?::TIMESTAMP
              AND timestamp <= ?::TIMESTAMP
            GROUP BY timestamp
        """
        
        params = list(nodes_to_query) + [start_time, end_time]

        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                results = conn.execute(query, params).fetchall()

            if not results:
                return {
                    "median_current_a": 0.0,
                    "median_current_b": 0.0,
                    "median_current_c": 0.0,
                    "total_kwh_delivered": 0.0,
                    "imbalance_delta": 0.0,
                    "peak_kwh_time": None,
                    "peak_kwh": 0.0,
                    "peak_current_a": 0.0,
                    "peak_current_b": 0.0,
                    "peak_current_c": 0.0,
                    "start_node_id": start_node_id,
                    "node_count": len(nodes_to_query),
                    "downstream_node_ids": nodes_to_query,
                    "downstream_edge_ids": downstream_edges
                }
                
            def get_median(lst):
                if not lst: return 0.0
                lst.sort()
                mid = len(lst) // 2
                if len(lst) % 2 == 0:
                    return (lst[mid - 1] + lst[mid]) / 2.0
                return lst[mid]
                
            current_a_list = [r[1] for r in results if r[1] is not None]
            current_b_list = [r[2] for r in results if r[2] is not None]
            current_c_list = [r[3] for r in results if r[3] is not None]
            
            median_a = get_median(current_a_list)
            median_b = get_median(current_b_list)
            median_c = get_median(current_c_list)
            
            # Simple imbalance metric: max difference between any two phases
            max_current = max(median_a, median_b, median_c)
            min_current = min(median_a, median_b, median_c)
            imbalance_delta = max_current - min_current
            
            total_kwh = sum((r[4] or 0.0) for r in results)
            
            # Find the peak energy interval and the phase currents at that time
            peak_row = max(results, key=lambda r: r[4] or 0.0)
            
            return {
                "median_current_a": median_a,
                "median_current_b": median_b,
                "median_current_c": median_c,
                "total_kwh_delivered": total_kwh,
                "imbalance_delta": imbalance_delta,
                "peak_kwh_time": peak_row[0].isoformat() if peak_row[0] else None,
                "peak_kwh": peak_row[4] or 0.0,
                "peak_current_a": peak_row[1] or 0.0,
                "peak_current_b": peak_row[2] or 0.0,
                "peak_current_c": peak_row[3] or 0.0,
                "start_node_id": start_node_id,
                "node_count": len(nodes_to_query),
                "downstream_node_ids": nodes_to_query,
                "downstream_edge_ids": downstream_edges
            }
        except Exception as e:
             return {"error": str(e)}
