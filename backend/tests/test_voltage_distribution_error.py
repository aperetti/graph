from unittest.mock import patch, MagicMock
from src.analytics.calculate_voltage import CalculateVoltageDistributionUseCase

def test_voltage_distribution_error():
    """Test voltage distribution error path by mocking a database failure."""
    graph_engine_mock = MagicMock()
    graph_engine_mock.find_downstream.return_value = (["M-3", "M-4"], ["E-3", "E-4"])

    uc = CalculateVoltageDistributionUseCase(graph_engine_mock, "dummy_db_path")

    with patch('duckdb.connect', side_effect=Exception("Database connection failed")):
        result = uc.execute("TX-B", "2020-01-01T00:00:00", "2030-01-01T00:00:00")

    assert "error" in result
    assert result["error"] == "Database connection failed"
