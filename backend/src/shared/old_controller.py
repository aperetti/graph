"""API Controller for the Analytical Agent and Graph Queries.

All topology data is served from the in-memory CIM-Graph FeederModel
(loaded at application startup).  SQLite is retained only for alarms.
DuckDB + Parquet remain the analytics engine for time-series queries.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

from src.shared.cim_model import CimModelManager
from src.shared.sqlite_repository import SqliteRepository
from src.grid.networkx_engine import NetworkXEngine
from src.discovery.discover_downstream import DiscoverDownstreamUseCase
from src.discovery.trace_upstream import TraceUpstreamUseCase
from src.analytics.calculate_voltage import CalculateVoltageDistributionUseCase
from src.analytics.phase_balancing import PhaseBalancingUseCase
from src.analytics.calculate_consumption import CalculateAggregateConsumptionUseCase
from src.analytics.map_voltage import MapVoltageUseCase
from src.analytics.get_alarms import GetActiveAlarmsUseCase
from src.agent.translate_nl_to_sql import AgentQueryProcessor
from src.shared.database_setup import DB_PATH, PARQUET_DIR, SQLITE_PATH

router = APIRouter()


@router.get("/estimate-test-unique")
async def estimate_test_unique():
    return {"status": "ok", "message": "unique route works"}


# ── Core dependencies ─────────────────────────────────────────────
# CIM model singleton (populated during FastAPI lifespan startup)
cim_manager = CimModelManager.get_instance()

# SQLite is kept only for alarms (generated offline by a separate script)
alarm_repo = SqliteRepository(SQLITE_PATH)

graph_engine = NetworkXEngine()
_graph_initialized = False


def _ensure_graph_built():
    """Build the NetworkX graph from the in-memory CIM model (lazy, once)."""
    global _graph_initialized
    if not _graph_initialized:
        from src.grid.graph_node import GraphNode

        # Pull topology directly from the CIM-Graph FeederModel
        nodes_raw = cim_manager.get_topology_nodes()
        edges = cim_manager.get_topology_edges()

        nodes = [
            GraphNode(
                id=n["node_id"],
                type=n["node_type"],
                name=n["name"] or n["node_id"],
                phases=n.get("phases_present") or ["A", "B", "C"],
                latitude=n["latitude"],
                longitude=n["longitude"],
                connected_equipment=n.get("connected_equipment", []),
                base_voltage_kv=n.get("base_voltage_kv"),
            )
            for n in nodes_raw
        ]

        graph_engine.build_graph(nodes=nodes, edges=edges)
        _graph_initialized = True


# ── Use cases (analytics still use DuckDB + Parquet) ──────────────
downstream_uc = DiscoverDownstreamUseCase(graph_engine)
upstream_uc = TraceUpstreamUseCase(graph_engine)
voltage_uc = CalculateVoltageDistributionUseCase(graph_engine, DB_PATH, PARQUET_DIR)
phase_uc = PhaseBalancingUseCase(graph_engine, DB_PATH, PARQUET_DIR)
consumption_uc = CalculateAggregateConsumptionUseCase(graph_engine, DB_PATH, PARQUET_DIR)
map_voltage_uc = MapVoltageUseCase(graph_engine, DB_PATH, PARQUET_DIR)
agent_processor = AgentQueryProcessor()

@router.get("/api/graph/downstream/{node_id}")
async def get_downstream(node_id: str):
    """Finds all downstream nodes."""
    _ensure_graph_built()
    return {"downstream_nodes": downstream_uc.execute(node_id)}

@router.get("/api/graph/upstream/{node_id}")
async def get_upstream(node_id: str):
    """Finds all upstream nodes."""
    _ensure_graph_built()
    return {"upstream_nodes": upstream_uc.execute(node_id)}

@router.get("/api/analytics/voltage/{node_id}/estimate")
async def get_voltage_estimate(
    node_id: str, 
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time"),
    degrees: int = Query(None, description="Degrees of separation for nearby node analysis")
):
    """Returns row count estimate for voltage distribution for one or more nodes (comma-separated)."""
    _ensure_graph_built()
    node_ids = node_id.split(",")
    return voltage_uc.estimate(node_ids, start_time, end_time, degrees=degrees)

@router.get("/api/analytics/voltage/{node_id}")
async def get_voltage_distribution(
    node_id: str, 
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time"),
    degrees: int = Query(None, description="Degrees of separation for nearby node analysis")
):
    """Calculates voltage distribution downstream of one or more nodes (comma-separated)."""
    _ensure_graph_built()
    node_ids = node_id.split(",")
    result = voltage_uc.execute(node_ids, start_time, end_time, degrees=degrees)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/api/analytics/phase-balance/{node_id}")
async def get_phase_balance(
    node_id: str, 
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time")
):
    """Calculates phase imbalance downstream of a node."""
    _ensure_graph_built()
    result = phase_uc.execute(node_id, start_time, end_time)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/api/analytics/consumption/{node_id}/estimate")
async def get_consumption_estimate(
    node_id: str, 
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time")
):
    """Returns row count estimate for consumption aggregation for one or more nodes (comma-separated)."""
    _ensure_graph_built()
    node_ids = node_id.split(",")
    return consumption_uc.estimate(node_ids, start_time, end_time)

@router.get("/api/analytics/consumption/{node_id}")
async def get_consumption(
    node_id: str, 
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time")
):
    """Calculates aggregate consumption for one or more nodes (comma-separated)."""
    _ensure_graph_built()
    node_ids = node_id.split(",")
    result = consumption_uc.execute(node_ids, start_time, end_time)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/api/analytics/map-voltage/estimate")
async def get_map_voltage_estimate(
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time"),
    agg: str = Query("median", description="Aggregation method: min, max, median, mean"),
    node_id: str = Query(None, description="Optional node to trace downstream from")
):
    """Returns row count estimate for map voltage summary."""
    _ensure_graph_built()
    return map_voltage_uc.estimate(start_time, end_time, agg, node_id)

@router.get("/api/analytics/map-voltage")
async def get_map_voltage(
    start_time: str = Query(..., description="ISO 8601 start time"), 
    end_time: str = Query(..., description="ISO 8601 end time"),
    agg: str = Query("median", description="Aggregation method: min, max, median, mean"),
    node_id: str = Query(None, description="Optional node to trace downstream from")
):
    """Calculates node voltage summary for the entire map or a subset."""
    _ensure_graph_built()
    result = await run_in_threadpool(map_voltage_uc.execute, start_time, end_time, agg, node_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/agent/query")
async def process_agent_query(query: str):
    """Translates NL to SQL or Graph queries."""
    # In a real app we'd get context based on currently selected nodes
    result = agent_processor.process_query(query)
    return {"generated_prompt": result}

@router.get("/api/graph/topology")
async def get_topology():
    """Returns the full grid topology with coordinates for UI rendering.

    All data is served from the in-memory CIM-Graph FeederModel.
    """
    _ensure_graph_built()
    nodes = cim_manager.get_topology_nodes()
    all_edges = cim_manager.get_topology_edges()

    # Trace circuits from Substations
    substations = [n['node_id'] for n in nodes if n['node_type'] == 'Substation']
    node_to_circuit = {}

    import networkx as nx
    undirected_graph = graph_engine.graph.to_undirected()

    components = list(nx.connected_components(undirected_graph))
    node_to_comp_idx = {}
    for idx, comp in enumerate(components):
        for node in comp:
            node_to_comp_idx[node] = idx

    comp_to_circuit = {}
    for i, sub_id in enumerate(substations):
        if sub_id in node_to_comp_idx:
            comp_to_circuit[node_to_comp_idx[sub_id]] = f"circuit_{i+1}"

    for comp_idx, circuit_id in comp_to_circuit.items():
        for node in components[comp_idx]:
            node_to_circuit[node] = circuit_id

    # Attach source and target coordinates to the edges for Deck.gl LineLayer
    node_coords = {
        n['node_id']: [n['longitude'], n['latitude']]
        for n in nodes if n['longitude'] and n['latitude']
    }

    # Map into Deck.GL format with enriched CIM attributes
    mapped_nodes = []
    for n in nodes:
        if n['longitude'] and n['latitude']:
            mapped_nodes.append({
                "id": n['node_id'],
                "type": n['node_type'],
                "name": n['name'],
                "position": [n['longitude'], n['latitude']],
                "circuit_id": node_to_circuit.get(n['node_id'], "unknown"),
                "is_open": n.get('is_open', False),
                "phases": n.get('phases_present', ['A', 'B', 'C']),
                "base_voltage_kv": n.get('base_voltage_kv'),
                "connected_equipment": n.get('connected_equipment', []),
            })

    mapped_edges = []
    for e in all_edges:
        src = e['from_node_id']
        tgt = e['to_node_id']
        if src in node_coords and tgt in node_coords:
            mapped_edges.append({
                "id": e.get('edge_id', f"{src}-{tgt}"),
                "source": src,
                "target": tgt,
                "sourcePosition": node_coords[src],
                "targetPosition": node_coords[tgt],
                "circuit_id": node_to_circuit.get(src, "unknown"),
                "phases": e.get('phases'),
                "conductor_type": e.get('conductor_type'),
            })

    return {"nodes": mapped_nodes, "edges": mapped_edges}


# ═══════════════════════════════════════════════════════════════════
# CIM Model endpoints – query the in-memory FeederModel directly
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/cim/classes")
async def get_cim_classes():
    """List all CIM classes loaded into memory with their object counts."""
    return cim_manager.get_cim_classes()


@router.get("/api/cim/equipment-by-class/{class_name}")
async def get_equipment_by_class(class_name: str):
    """List all equipment objects of a given CIM class (e.g. ACLineSegment)."""
    items = cim_manager.get_all_equipment_by_class(class_name)
    if not items:
        raise HTTPException(status_code=404, detail=f"No objects found for class '{class_name}'")
    return {"class": class_name, "count": len(items), "items": items}


@router.get("/api/cim/equipment/{mrid}")
async def get_equipment_detail(mrid: str):
    """Full CIM detail for any equipment by mRID (impedances, ratings, windings, etc.)."""
    detail = cim_manager.get_equipment_detail(mrid)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Equipment not found: {mrid}")
    return detail


@router.get("/api/cim/node/{node_id}")
async def get_node_cim_details(node_id: str):
    """Enriched CIM details for a connectivity node and all its connected equipment."""
    detail = cim_manager.get_node_cim_details(node_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Connectivity node not found: {node_id}")
    return detail


@router.get("/discovery/alarms/{node_id}")
async def get_node_alarms(node_id: str, include_downstream: bool = Query(True)):
    """Fetch active alarms for a node and optionally its downstream children."""
    use_case = GetActiveAlarmsUseCase(alarm_repo, graph_engine)
    alarms = use_case.execute(node_id, include_downstream)
    return [a.dict() for a in alarms]
