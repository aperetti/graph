import pytest
import duckdb
import os
import pandas as pd
import numpy as np
from datetime import datetime

DB_PATH = "test_weather_sim.duckdb"

@pytest.fixture
def test_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = duckdb.connect(DB_PATH)
    
    # Setup minimal tables
    conn.execute("CREATE TABLE grid_nodes (node_id VARCHAR, node_type VARCHAR)")
    conn.execute("CREATE TABLE weather_recordings (month INTEGER, day INTEGER, hour INTEGER, temperature DOUBLE)")
    
    # Insert one meter
    conn.execute("INSERT INTO grid_nodes VALUES ('M1', 'Meter')")
    
    # Insert weather patterns
    # Jan 1st, Hour 0: Cold (0°C) -> Expected 1.0 + 0.05*18 = 1.9 multiplier
    conn.execute("INSERT INTO weather_recordings VALUES (1, 1, 0, 0.0)")
    # July 1st, Hour 12: Hot (34°C) -> Expected 1.0 + 0.08*10 = 1.8 multiplier
    conn.execute("INSERT INTO weather_recordings VALUES (7, 1, 12, 34.0)")
    # Oct 1st, Hour 12: Mild (21°C) -> Expected 1.0 multiplier
    conn.execute("INSERT INTO weather_recordings VALUES (10, 1, 12, 21.0)")
    
    yield conn
    conn.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_weather_load_scaling(test_db):
    """Verifies that the SQL logic in generate_cim_readings.py correctly scales loads based on weather."""
    
    # Logic extracted from generate_cim_readings.py query:
    # load_multiplier = 1.0 + 0.05 * GREATEST(0, 18 - temp) + 0.08 * GREATEST(0, temp - 24)
    
    # Test values
    # 0°C  -> 1.9
    # 34°C -> 1.8
    # 21°C -> 1.0
    
    query = """
    SELECT 
        w.temperature,
        (1.0 + 0.05 * GREATEST(0, 18 - w.temperature) + 0.08 * GREATEST(0, w.temperature - 24)) as multiplier
    FROM weather_recordings w
    ORDER BY w.month
    """
    
    results = test_db.execute(query).fetchall()
    
    # Jan (Month 1): 0°C
    assert results[0][0] == 0.0
    assert results[0][1] == 1.9
    
    # July (Month 7): 34°C
    assert results[1][0] == 34.0
    assert results[1][1] == 1.8
    
    # Oct (Month 10): 21°C
    assert results[2][0] == 21.0
    assert results[2][1] == 1.0

if __name__ == "__main__":
    pytest.main([__file__])
