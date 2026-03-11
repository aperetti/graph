"""Use Case: Aggregate Consumption Analytics."""
import duckdb
from typing import Dict, Any, List
from src.shared.graph_engine import GraphEngine

class CalculateAggregateConsumptionUseCase:
    """Aggregates kwh_dlv and kwh_rcv over time for downstream meters."""
    
    def __init__(self, graph_engine: GraphEngine, db_path: str, parquet_dir: str = 'readings'):
        self.graph_engine = graph_engine
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        
    def execute(self, start_node_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """
        Aggregates consumption data grouped by timestamp.
        
        Args:
            start_node_id: The asset to evaluate.
            start_time: ISO timestamp string.
            end_time: ISO timestamp string.
            
        Returns:
            Dictionary with time-series consumption data.
        """
        downstream_nodes, downstream_edges = self.graph_engine.find_downstream(start_node_id)
        
        # If no downstream (leaf node like a Meter), query the node itself
        nodes_to_query = downstream_nodes if downstream_nodes else [start_node_id]
        
        # Format for SQL IN clause
        nodes_list = "'" + "','".join(nodes_to_query) + "'"
        
        query = f"""
            SELECT 
                r.timestamp,
                SUM(COALESCE(r.kwh_dlv, 0)) as total_kwh_dlv,
                SUM(COALESCE(r.current_a, 0) + COALESCE(r.current_b, 0) + COALESCE(r.current_c, 0)) as total_current,
                MEDIAN(r.voltage_a) as median_volts_a,
                MEDIAN(r.voltage_b) as median_volts_b,
                MEDIAN(r.voltage_c) as median_volts_c,
                MAX(w.temperature) as temperature
            FROM read_parquet('{self.parquet_dir}/*.parquet') r
            LEFT JOIN weather_recordings w 
                ON w.month = EXTRACT(month FROM r.timestamp)
                AND w.day = EXTRACT(day FROM r.timestamp)
                AND w.hour = EXTRACT(hour FROM r.timestamp)
            WHERE r.node_id IN ({nodes_list})
              AND r.timestamp >= '{start_time}' 
              AND r.timestamp <= '{end_time}'
            GROUP BY r.timestamp
            ORDER BY r.timestamp ASC
        """
        
        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                results = conn.execute(query).fetchall()
                
            time_series = [
                {
                    "timestamp": row[0].isoformat() + "Z",
                    "kwh_delivered": row[1],
                    "total_current": row[2],
                    "median_voltage_a": row[3],
                    "median_voltage_b": row[4],
                    "median_voltage_c": row[5],
                    "temperature": row[6]
                }
                for row in results
            ]
            
            return {
                "start_node_id": start_node_id,
                "node_count": len(nodes_to_query),
                "downstream_node_ids": nodes_to_query,
                "downstream_edge_ids": downstream_edges,
                "time_series": time_series
            }
        except Exception as e:
             return {"error": str(e)}
