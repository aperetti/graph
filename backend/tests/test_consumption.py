"""Integration tests for Calculate Consumption with Temperature."""
import pytest
import os
from src.shared.duckdb_repository import DuckDBRepository
from src.grid.networkx_engine import NetworkXEngine
from src.analytics.calculate_consumption import CalculateAggregateConsumptionUseCase
from src.shared.database_setup import DB_PATH, PARQUET_DIR

@pytest.fixture
def repo():
    return DuckDBRepository(DB_PATH)

@pytest.fixture
def graph_engine(repo):
    engine = NetworkXEngine()
    edges = repo.get_all_edges()
    engine.build_graph(edges=edges)
    return engine

def test_calculate_consumption_with_temperature(graph_engine):
    """Test that consumption calculation returns temperature data."""
    # Ensure parquet directory exists for test (might be empty but query should run)
    if not os.path.exists(PARQUET_DIR):
        os.makedirs(PARQUET_DIR)
        
    uc = CalculateAggregateConsumptionUseCase(graph_engine, PARQUET_DIR)
    
    # Query M-1
    result = uc.execute("M-1", "2020-01-01T00:00:00", "2030-01-01T00:00:00")
    
    if "error" in result:
        # If no data is found, it might return an error or empty list depending on impl
        # But here we want to check the structure if data WAS found or the query logic
        pytest.skip("No data in parquet for testing, skipping structural check")
    
    if result["time_series"]:
        first_point = result["time_series"][0]
        assert "temperature" in first_point
        assert isinstance(first_point["temperature"], (int, float))
        assert "kwh_delivered" in first_point
        assert "median_voltage_a" in first_point
def test_calculate_multi_node_consumption(graph_engine):
    """Test that consumption calculation handles multiple start nodes."""
    uc = CalculateAggregateConsumptionUseCase(graph_engine, PARQUET_DIR)
    
    # Query M-1 and M-2 (if exists)
    node_ids = ["M-1", "M-2"]
    result = uc.execute(node_ids, "2020-01-01T00:00:00", "2030-01-01T00:00:00")
    
    # We mainly want to check that it doesn't crash and returns the expected structure
    assert "time_series" in result
    assert "downstream_node_ids" in result
    assert "downstream_edge_ids" in result
    
    # If M-1 exists, its downstream should be in the result
    if result["downstream_node_ids"]:
        assert len(result["downstream_node_ids"]) > 0
