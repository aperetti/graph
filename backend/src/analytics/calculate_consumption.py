"""Use Case: Aggregate Consumption Analytics."""
import duckdb
from typing import Dict, Any, List
from src.shared.graph_engine import GraphEngine

class CalculateAggregateConsumptionUseCase:
    """Aggregates kwh_dlv and kwh_rcv over time for downstream meters."""
    
    def __init__(self, graph_engine: GraphEngine, db_path: str, parquet_dir: str = 'readings'):
        self.graph_engine = graph_engine
        # Handle case where db_path might be same as parquet_dir (for tests)
        self.db_path = db_path
        self.parquet_dir = parquet_dir if parquet_dir else db_path
        
    def estimate(self, start_node_ids: List[str], start_time: str, end_time: str) -> Dict[str, Any]:
        """Returns the estimated number of rows to be processed for multiple nodes."""
        all_downstream_nodes = set()
        for node_id in start_node_ids:
            nodes, _ = self.graph_engine.find_downstream(node_id)
            if nodes:
                all_downstream_nodes.update(nodes)
            else:
                all_downstream_nodes.add(node_id)
        
        nodes_to_query = list(all_downstream_nodes)
        placeholders = ",".join(["?"] * len(nodes_to_query))
        query_params = nodes_to_query + [start_time, end_time]
        
        prefetch_query = f"""
            SELECT COUNT(*) as estimated_rows
            FROM read_parquet('{self.parquet_dir}/*.parquet') r
            WHERE r.node_id IN ({placeholders})
              AND r.timestamp >= CAST(? AS TIMESTAMP)
              AND r.timestamp <= CAST(? AS TIMESTAMP)
        """
        
        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                prefetch_results = conn.execute(prefetch_query, query_params).fetchone()
            
            return {
                "estimated_rows": prefetch_results[0] if prefetch_results else 0,
                "node_count": len(nodes_to_query)
            }
        except Exception as e:
            return {"error": str(e)}

    def execute(self, start_node_ids: List[str], start_time: str, end_time: str) -> Dict[str, Any]:
        """
        Aggregates consumption data grouped by timestamp for multiple start nodes.
        """
        all_downstream_nodes = set()
        all_downstream_edges = set()
        
        for node_id in start_node_ids:
            nodes, edges = self.graph_engine.find_downstream(node_id)
            if nodes:
                all_downstream_nodes.update(nodes)
            else:
                all_downstream_nodes.add(node_id)
            if edges:
                all_downstream_edges.update(edges)
        
        nodes_to_query = list(all_downstream_nodes)
        placeholders = ",".join(["?"] * len(nodes_to_query))
        query_params = nodes_to_query + [start_time, end_time]
        
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
            WHERE r.node_id IN ({placeholders})
              AND r.timestamp >= CAST(? AS TIMESTAMP)
              AND r.timestamp <= CAST(? AS TIMESTAMP)
            GROUP BY r.timestamp
            ORDER BY r.timestamp ASC
        """
        
        try:
            with duckdb.connect(self.db_path, read_only=True) as conn:
                results = conn.execute(query, query_params).fetchall()
                
            time_series = [
                {
                    "timestamp": row[0].isoformat() + "Z",
                    "kwh_delivered": float(row[1]),
                    "total_current": float(row[2]),
                    "median_voltage_a": float(row[3]) if row[3] else 0,
                    "median_voltage_b": float(row[4]) if row[4] else 0,
                    "median_voltage_c": float(row[5]) if row[5] else 0,
                    "temperature": float(row[6]) if row[6] else 0
                }
                for row in results
            ]
            
            return {
                "start_node_ids": start_node_ids,
                "node_count": len(nodes_to_query),
                "downstream_node_ids": nodes_to_query,
                "downstream_edge_ids": list(all_downstream_edges),
                "time_series": time_series
            }
        except Exception as e:
             return {"error": str(e)}
