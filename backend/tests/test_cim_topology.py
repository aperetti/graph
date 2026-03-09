import pytest
import os
import duckdb
from src.shared.duckdb_repository import DuckDBRepository
from src.grid.networkx_engine import NetworkXEngine
from src.discovery.discover_downstream import DiscoverDownstreamUseCase

DB_PATH = "grid_data.duckdb"

def test_cim_topology_ingestion():
    # If the database doesn't exist, we might not have run the CIM script yet
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Database {DB_PATH} not found. Run ingest_cim.py first.")
        
    repo = DuckDBRepository(DB_PATH)
    graph_engine = NetworkXEngine()
    
    edges = repo.get_all_edges()
    assert len(edges) > 1000, "CIM Ingestion should have produced >1000 edges"
    
    graph_engine.build_graph(edges=edges)
    
    # Let's find a valid source node. Since Substations got genericized or not linked cleanly,
    # let's find the first node that only has OUTGOING edges.
    conn = duckdb.connect(DB_PATH)
    # Roots in a radial circuit have 0 incoming edges
    res = conn.execute("""
        SELECT e.from_node_id 
        FROM grid_edges e
        LEFT JOIN grid_edges incoming ON incoming.to_node_id = e.from_node_id
        WHERE incoming.to_node_id IS NULL
        LIMIT 1
    """).fetchone()
    conn.close()
    
    assert res is not None, "Could not identify a clear topological root in the CIM network"
    root_id = res[0]
    
    print(f"Tracing downstream from CIM topological root: {root_id}")
    uc_downstream = DiscoverDownstreamUseCase(graph_engine)
    downstream_nodes = uc_downstream.execute(root_id)
    
    # We should have identified a significant subnet
    print(f"Discovered {len(downstream_nodes)} downstream nodes")
    assert len(downstream_nodes) > 10, "Trace failed to identify a deep topological tree"
    
    # 3. Test Phase Balancing capability
    from src.analytics.phase_balancing import PhaseBalancingUseCase
    # Creating a small synthetic parquet dataset for the CIM nodes so we can test the SQL analytics
    import pandas as pd
    import numpy as np
    
    # Extract just the meter node IDs since they get readings
    conn = duckdb.connect(DB_PATH)
    # Using SQL to filter the list since graph_engine only tracks topology, not node metadata
    # We pass the python list to DuckDB
    # Convert list to tuple string for SQL IN clause
    nodes_str = "'" + "','".join(downstream_nodes) + "'"
    meter_res = conn.execute(f"SELECT node_id FROM grid_nodes WHERE node_type = 'Meter' AND node_id IN ({nodes_str})").fetchall()
    meter_ids = [r[0] for r in meter_res]
    conn.close()
    
    if len(meter_ids) > 0 and len(meter_ids) < 2000:
        # Generate 1 hour of data for these nodes if there aren't too many
        print(f"Generating synthetic readings for {len(meter_ids)} CIM meters...")
        readings = []
        for mid in meter_ids:
            # 4 readings representing 1 hour (15min intervals)
            for i in range(4):
                readings.append({
                    'node_id': mid,
                    'timestamp': pd.Timestamp('2025-01-01 00:00:00') + pd.Timedelta(minutes=15*i),
                    'voltage_a': np.random.normal(120, 2),
                    'voltage_b': np.random.normal(120, 2),
                    'voltage_c': np.random.normal(120, 2),
                    'current_a': np.random.normal(10, 2),
                    'current_b': np.random.normal(10, 2),
                    'current_c': np.random.normal(10, 2),
                    'kwh_dlv': np.random.uniform(0.1, 2.0)
                })
        df = pd.DataFrame(readings)
        os.makedirs("cim_readings", exist_ok=True)
        df.to_parquet("cim_readings/test_cim.parquet", engine='pyarrow')
        
        print("Executing Phase Balancing...")
        uc_phase = PhaseBalancingUseCase(graph_engine, DB_PATH, "cim_readings")
        res = uc_phase.execute(root_id, "2025-01-01T00:00:00", "2025-01-01T01:00:00")
        assert "error" not in res
        print(f"Phase balance results: {res}")
        
    print("CIM Topology Analytics verified!")
