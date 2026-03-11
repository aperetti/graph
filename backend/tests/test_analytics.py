"""Integration tests for Graph Discovery and Analytics using DuckDB/Parquet."""
import pytest
from src.shared.duckdb_repository import DuckDBRepository
from src.grid.networkx_engine import NetworkXEngine
from src.discovery.discover_downstream import DiscoverDownstreamUseCase
from src.analytics.calculate_voltage import CalculateVoltageDistributionUseCase
from src.analytics.phase_balancing import PhaseBalancingUseCase
from src.shared.database_setup import DB_PATH

@pytest.fixture
def repo():
    return DuckDBRepository(DB_PATH)

@pytest.fixture
def graph_engine(repo):
    engine = NetworkXEngine()
    
    # Normally we'd fetch nodes too, but edges construct the graph
    edges = repo.get_all_edges()
    engine.build_graph(edges=edges)
    return engine

def test_downstream_discovery(graph_engine):
    """Test discovering meters downstream of a transformer."""
    uc = DiscoverDownstreamUseCase(graph_engine)
    
    # From our mock data, TX-A should feed M-1 and M-2
    downstream, downstream_edges = uc.execute("TX-A")
    assert "M-1" in downstream
    assert "M-2" in downstream
    assert len(downstream) == 2

def test_voltage_distribution(graph_engine):
    """Test voltage distribution across a transformer."""
    uc = CalculateVoltageDistributionUseCase(graph_engine, DB_PATH, parquet_dir="cim_readings")
    
    # Query TX-B (feeds M-3 and M-4)
    # Using a wide time range to catch our mock data
    result = uc.execute("TX-B", "2020-01-01T00:00:00", "2030-01-01T00:00:00")
    
    assert "error" not in result
    assert result["node_count"] == 2
    assert len(result["distribution"]) > 0

def test_phase_balancing(graph_engine):
    """Test phase balancing across the main substation."""
    uc = PhaseBalancingUseCase(graph_engine, DB_PATH, parquet_dir="cim_readings")
    
    # Query SUB-1 (feeds everything)
    result = uc.execute("SUB-1", "2020-01-01T00:00:00", "2030-01-01T00:00:00")
    
    assert "error" not in result
    assert result["node_count"] == 6 # TX-A, TX-B, M-1, M-2, M-3, M-4
    assert result["median_current_a"] > 0
    assert result["median_current_b"] > 0
    assert result["median_current_c"] > 0
    assert result["imbalance_delta"] >= 0

def test_phase_balancing_error_path(graph_engine):
    """Test error handling in phase balancing by using an invalid database path."""
    # Provide an invalid db_path to trigger the exception block
    uc = PhaseBalancingUseCase(graph_engine, db_path="/invalid/path/db.duckdb")

    result = uc.execute("SUB-1", "2020-01-01T00:00:00", "2030-01-01T00:00:00")

    assert "error" in result
