import os
import duckdb

def get_db_connection() -> duckdb.DuckDBPyConnection:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "grid_data_cim.duckdb")
    return duckdb.connect(db_path, read_only=True)

def test_diurnal_variation():
    """
    Ensure there's a significant difference between daytime and nighttime 
    average energy consumption, confirming the diurnal profiles.
    """
    conn = get_db_connection()
    parquet_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cim_readings")
    
    # Check if there are readings to test
    if not os.path.exists(parquet_dir) or not [f for f in os.listdir(parquet_dir) if f.endswith('.parquet')]:
        return # Skip if data hasn't been generated yet
        
    query = f"""
    SELECT 
        date_part('hour', timestamp) as hr,
        AVG(kwh_dlv) * 4 as avg_kw
    FROM read_parquet('{parquet_dir}/*.parquet')
    GROUP BY hr
    ORDER BY hr
    """
    
    results = conn.execute(query).fetchall()
    
    # Extract kW by hour
    kw_by_hour = {int(row[0]): float(row[1]) for row in results}
    
    # Calculate average night (0-5)
    night_avg = sum(kw_by_hour[h] for h in range(0, 6)) / 6
    
    # Calculate average daytime (8-20)
    day_avg = sum(kw_by_hour[h] for h in range(8, 21)) / 13
    
    print(f"Average night consumption: {night_avg:.3f} kW")
    print(f"Average day consumption: {day_avg:.3f} kW")
    
    # Assert there is a nocturnal dip (night avg should be lower than day avg)
    assert night_avg < day_avg, "Expected nighttime consumption to be lower than daytime consumption"
    
    # In our model, day should be at least 30% higher than night overall
    assert day_avg > night_avg * 1.3, "Expected daytime peak to be > 30% higher than nocturnal baseline"
    print("Diurnal variation test passed!")
    
if __name__ == "__main__":
    test_diurnal_variation()
