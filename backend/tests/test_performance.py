"""Performance test suite to verify DuckDB Parquet aggregation latency."""
import time
from src.shared.duckdb_repository import DuckDBRepository
from src.grid.networkx_engine import NetworkXEngine
from src.discovery.discover_downstream import DiscoverDownstreamUseCase
from src.analytics.calculate_voltage import CalculateVoltageDistributionUseCase
from src.analytics.phase_balancing import PhaseBalancingUseCase
DB_PATH = "grid_data_scale.duckdb"
PARQUET_DIR = "readings_scale"

def test_scale_performance():
    print("Initializing Graph Engine...")
    start_time = time.time()
    repo = DuckDBRepository(DB_PATH)
    graph_engine = NetworkXEngine()
    
    edges = repo.get_all_edges()
    graph_engine.build_graph(edges=edges)
    end_time = time.time()
    print(f"Graph with {len(edges)} edges built in {end_time - start_time:.4f} seconds.")

    # 1. Downstream Discovery (Graph Traversal)
    print("\nTracing downstream for SUB-1 (Entire Grid 100k+ meters)")
    start_time = time.time()
    uc_downstream = DiscoverDownstreamUseCase(graph_engine)
    downstream_nodes = uc_downstream.execute("SUB-1")
    end_time = time.time()
    print(f"Discovered {len(downstream_nodes)} downstream nodes in {end_time - start_time:.4f} seconds.")

    # 2. Analytics
    # Calculate Phase Balance for the entire grid over a whole year
    print("\nCalculating Phase Imbalance over 1 year for 100k meters...")
    start_time = time.time()
    uc_phase = PhaseBalancingUseCase(graph_engine, DB_PATH, PARQUET_DIR)
    
    # Run the query. It will sum up reading stats for all 100k meters for a year.
    res = uc_phase.execute("SUB-1", "2025-01-01T00:00:00", "2026-01-01T00:00:00")
    end_time = time.time()
    print(f"Phase balance calculation completed in {end_time - start_time:.4f} seconds.")
    if "error" in res:
        print("Error:", res["error"])
    else:
        print(f"Results: Total MWh: {res['total_kwh_delivered']/1000:,.2f} MWh, Imbalance Delta: {res['imbalance_delta']:,.2f} A")

if __name__ == "__main__":
    test_scale_performance()
