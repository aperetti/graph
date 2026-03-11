"""Use Case: Voltage Distribution."""
from overrides import overrides
import duckdb
from typing import Dict, Any, List
from src.shared.graph_engine import GraphEngine

class CalculateVoltageDistributionUseCase:
    """Calculates voltage statistics (mean, median, stddev) for downstream meters."""
    
    def __init__(self, graph_engine: GraphEngine, db_path: str, parquet_dir: str = 'readings'):
        self.graph_engine = graph_engine
        self.db_path = db_path
        self.parquet_dir = parquet_dir
        
    def execute(self, start_node_id: str, start_time: str, end_time: str, degrees: int = None) -> Dict[str, Any]:
        """
        Executes the voltage distribution query.
        
        Args:
            start_node_id: The device to start from (e.g., a Transformer).
            start_time: ISO timestamp string.
            end_time: ISO timestamp string.
            degrees: Optional degree limit for the search.
            
        Returns:
            Dictionary with statistical results.
        """
        downstream_nodes, downstream_edges = self.graph_engine.find_downstream(start_node_id, max_depth=degrees)
        
        # If no downstream (leaf node like a Meter), query the node itself
        nodes_to_query = downstream_nodes if downstream_nodes else [start_node_id]
            
        # In DuckDB, to parameterize timestamps in a query against Parquet files
        # using a simple string might fail if not casted to timestamp explicitly,
        # so we cast parameters explicitly to avoid 'Cannot compare values of type TIMESTAMP and type VARCHAR'

        # Format for SQL IN clause placeholders
        placeholders = ",".join(["?"] * len(nodes_to_query))
        
        query = f"""
            WITH a_bins AS (
                SELECT ROUND(voltage_a * 2) / 2.0 as v_bin, COUNT(*) as cnt_a
                FROM read_parquet('{self.parquet_dir}/*.parquet')
                WHERE node_id IN ({placeholders})
                  AND timestamp >= CAST(? AS TIMESTAMP)
                  AND timestamp <= CAST(? AS TIMESTAMP)
                  AND voltage_a IS NOT NULL
                GROUP BY 1
            ),
            b_bins AS (
                SELECT ROUND(voltage_b * 2) / 2.0 as v_bin, COUNT(*) as cnt_b
                FROM read_parquet('{self.parquet_dir}/*.parquet')
                WHERE node_id IN ({placeholders})
                  AND timestamp >= CAST(? AS TIMESTAMP)
                  AND timestamp <= CAST(? AS TIMESTAMP)
                  AND voltage_b IS NOT NULL
                GROUP BY 1
            ),
            c_bins AS (
                SELECT ROUND(voltage_c * 2) / 2.0 as v_bin, COUNT(*) as cnt_c
                FROM read_parquet('{self.parquet_dir}/*.parquet')
                WHERE node_id IN ({placeholders})
                  AND timestamp >= CAST(? AS TIMESTAMP)
                  AND timestamp <= CAST(? AS TIMESTAMP)
                  AND voltage_c IS NOT NULL
                GROUP BY 1
            ),
            all_bins AS (
                SELECT v_bin FROM a_bins
                UNION
                SELECT v_bin FROM b_bins
                UNION
                SELECT v_bin FROM c_bins
            )
            SELECT 
                all_bins.v_bin as voltage,
                COALESCE(a_bins.cnt_a, 0) as phase_a_count,
                COALESCE(b_bins.cnt_b, 0) as phase_b_count,
                COALESCE(c_bins.cnt_c, 0) as phase_c_count
            FROM all_bins
            LEFT JOIN a_bins ON all_bins.v_bin = a_bins.v_bin
            LEFT JOIN b_bins ON all_bins.v_bin = b_bins.v_bin
            LEFT JOIN c_bins ON all_bins.v_bin = c_bins.v_bin
            ORDER BY voltage ASC
        """
        heatmap_query = f"""
            SELECT * FROM (
                WITH total_loading AS (
                    SELECT timestamp, SUM(kwh_dlv) as total_kwh
                    FROM read_parquet('{self.parquet_dir}/*.parquet')
                    WHERE node_id IN ({placeholders})
                      AND timestamp >= CAST(? AS TIMESTAMP)
                      AND timestamp <= CAST(? AS TIMESTAMP)
                    GROUP BY timestamp
                )
                SELECT 
                    t.total_kwh as loading,
                    r.voltage_a as voltage,
                    CAST(COUNT(*) AS INTEGER) as cnt
                FROM read_parquet('{self.parquet_dir}/*.parquet') r
                JOIN total_loading t ON r.timestamp = t.timestamp
                WHERE r.node_id IN ({placeholders})
                  AND r.timestamp >= CAST(? AS TIMESTAMP)
                  AND r.timestamp <= CAST(? AS TIMESTAMP)
                  AND r.voltage_a IS NOT NULL
                  AND t.total_kwh IS NOT NULL
                GROUP BY 1, 2
            ) USING SAMPLE reservoir(10000)
        """
        
        timeseries_query = f"""
            SELECT 
                CAST(timestamp AS DATE) as day,
                MEDIAN(voltage_a) as p50,
                QUANTILE_CONT(voltage_a, 0.1) as p10,
                QUANTILE_CONT(voltage_a, 0.9) as p90
            FROM read_parquet('{self.parquet_dir}/*.parquet')
            WHERE node_id IN ({placeholders})
              AND timestamp >= CAST(? AS TIMESTAMP)
              AND timestamp <= CAST(? AS TIMESTAMP)
              AND voltage_a IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """

        try:
            # Parameters for main query (used 3 times in a_bins, b_bins, c_bins)
            base_params = nodes_to_query + [start_time, end_time]
            query_params = base_params * 3

            # Parameters for heatmap query (used 2 times)
            heatmap_params = base_params * 2

            # Parameters for timeseries query (used 1 time)
            timeseries_params = base_params

            with duckdb.connect(self.db_path, read_only=True) as conn:
                results = conn.execute(query, query_params).fetchall()
                heat_results = conn.execute(heatmap_query, heatmap_params).fetchall()
                ts_results = conn.execute(timeseries_query, timeseries_params).fetchall()
                
            distribution = []
            for row in results:
                distribution.append({
                    "voltage": float(row[0]),
                    "phase_a": int(row[1]),
                    "phase_b": int(row[2]),
                    "phase_c": int(row[3])
                })
                
            scatter = [
                {"voltage": float(row[1]), "loading": float(row[0]), "count": int(row[2])}
                for row in heat_results
            ]

            timeseries = [
                {
                    "date": row[0].isoformat(),
                    "p50": float(row[1]),
                    "p10": float(row[2]),
                    "p90": float(row[3])
                }
                for row in ts_results
            ]
                
            return {
                "start_node_id": start_node_id,
                "node_count": len(nodes_to_query),
                "downstream_node_ids": nodes_to_query,
                "downstream_edge_ids": downstream_edges,
                "distribution": distribution,
                "scatter": scatter,
                "timeseries": timeseries
            }
        except Exception as e:
             return {"error": str(e)}
