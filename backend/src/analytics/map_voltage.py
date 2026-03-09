"""Use Case: Map Voltage View."""
from typing import Dict, Any, Optional
import duckdb
from src.shared.graph_engine import GraphEngine

class MapVoltageUseCase:
    """Calculates voltage aggregations (min, max, median) for map visualization."""
    
    def __init__(self, graph_engine: GraphEngine, db_path: str, parquet_dir: str = 'readings'):
        self.graph_engine = graph_engine
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        
    def execute(self, start_time: str, end_time: str, agg: str, start_node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the voltage aggregation query.
        
        Args:
            start_time: ISO timestamp string.
            end_time: ISO timestamp string.
            agg: The aggregation type ('min', 'max', 'median')
            start_node_id: Optional device to start from. If None, queries all.
            
        Returns:
            Dictionary with node_voltages mapping.
        """
        nodes_list_filter = ""
        nodes_to_query = []
        if start_node_id:
            downstream_nodes, _ = self.graph_engine.find_downstream(start_node_id)
            nodes_to_query = downstream_nodes if downstream_nodes else [start_node_id]
            nodes_list_str = "'" + "','".join(nodes_to_query) + "'"
            nodes_list_filter = f"AND node_id IN ({nodes_list_str})"

        agg_func = "AVG"
        if agg == "min":
            agg_func = "MIN"
        elif agg == "max":
            agg_func = "MAX"
        elif agg == "median":
            # DuckDB median
            agg_func = "MEDIAN"
            
        node_avg_query = f"""
            SELECT node_id, {agg_func}(voltage_a) as v
            FROM read_parquet('{self.parquet_dir}/*.parquet')
            WHERE timestamp >= '{start_time}'
              AND timestamp <= '{end_time}'
              AND voltage_a IS NOT NULL
              {nodes_list_filter}
            GROUP BY node_id
        """
        
        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                node_avg_results = conn.execute(node_avg_query).fetchall()
                
            node_voltages = {row[0]: float(row[1]) for row in node_avg_results if row[1] is not None}
                
            return {
                "start_node_id": start_node_id,
                "node_count": len(node_voltages),
                "node_voltages": node_voltages,
                "agg": agg
            }
        except Exception as e:
             return {"error": str(e)}
