#!/usr/bin/env python3
"""
CIM-Graph based CIM XML ingestion → SQLite topology database.

Replaces the custom XML parsing in ingest_cim.py with the PNNL CIM-Graph
library (https://github.com/PNNL-CIM-Tools/CIM-Graph).

Usage:
    python scripts/ingest_cim_graph.py
    CIM_MODEL_PATH=sample_data/IEEE8500.xml python scripts/ingest_cim_graph.py
"""
import os
import sys
import sqlite3
import json
import random
from pathlib import Path
from collections import defaultdict

# ── CIM-Graph environment (must be set before importing cimgraph) ──
os.environ.setdefault('CIMG_CIM_PROFILE', 'rc4_2021')
os.environ.setdefault('CIMG_IEC61970_301', '8')  # rdf:about with urn:uuid:

SCRIPT_PATH = Path(__file__).resolve()
BACKEND_DIR = SCRIPT_PATH.parents[1]
WORKSPACE_ROOT = SCRIPT_PATH.parents[2]

SQLITE_PATH = os.getenv(
    "TOPOLOGY_DB_PATH", str(WORKSPACE_ROOT / "grid_topology.sqlite")
)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def resolve_xml_path() -> Path:
    """Resolve CIM XML file path from env var or known project locations."""
    env_xml = os.getenv("CIM_MODEL_PATH")
    if env_xml:
        p = Path(env_xml)
        if p.is_file():
            return p
        cwd_resolved = (Path.cwd() / p).resolve()
        if cwd_resolved.is_file():
            return cwd_resolved

    candidates = [
        BACKEND_DIR / "sample_data" / "IEEE8500_3subs.xml",
        BACKEND_DIR / "sample_data" / "IEEE8500.xml",
        WORKSPACE_ROOT / "backend" / "sample_data" / "IEEE8500.xml",
    ]
    for c in candidates:
        if c.is_file():
            return c

    return BACKEND_DIR / "sample_data" / "IEEE8500.xml"


# ---------------------------------------------------------------------------
# SQLite setup
# ---------------------------------------------------------------------------

def setup_sqlite(db_path: str) -> sqlite3.Connection:
    """Create / reset the SQLite topology database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.execute("DROP TABLE IF EXISTS grid_edges")
    conn.execute("DROP TABLE IF EXISTS grid_nodes")

    conn.execute("""
        CREATE TABLE grid_nodes (
            node_id   TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            name      TEXT,
            phases_present TEXT DEFAULT '["A","B","C"]',
            latitude  REAL,
            longitude REAL,
            is_open   INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE grid_edges (
            edge_id      TEXT PRIMARY KEY,
            from_node_id TEXT NOT NULL REFERENCES grid_nodes(node_id),
            to_node_id   TEXT NOT NULL REFERENCES grid_nodes(node_id),
            conductor_type TEXT,
            phases       TEXT DEFAULT '["A","B","C"]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            alarm_id  TEXT PRIMARY KEY,
            node_id   TEXT,
            timestamp TEXT,
            alarm_code TEXT,
            severity  TEXT,
            message   TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# CIM-Graph helpers
# ---------------------------------------------------------------------------

def mrid_str(obj) -> str | None:
    """Safely extract mRID as a plain string (strip urn:uuid: / _ prefix)."""
    if obj is None:
        return None
    m = getattr(obj, 'mRID', None)
    if m is None:
        return None
    s = str(m)
    for prefix in ('urn:uuid:', '_'):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def get_name(obj) -> str:
    """Get the IdentifiedObject.name, falling back to mRID."""
    name = getattr(obj, 'name', None)
    return name if name else (mrid_str(obj) or "Unknown")


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def main():
    xml_path = resolve_xml_path()
    print(f"SQLite DB : {SQLITE_PATH}")
    print(f"CIM XML   : {xml_path}")

    if not xml_path.is_file():
        print(f"ERROR: XML file not found: {xml_path}", file=sys.stderr)
        sys.exit(1)

    # ── 1. Load CIM model with CIM-Graph ──────────────────────────
    print("\nLoading CIM model with CIM-Graph...")

    import cimgraph.data_profile.rc4_2021 as cim
    from cimgraph.databases import XMLFile
    from cimgraph.models import FeederModel

    xml_file = XMLFile(filename=str(xml_path))
    network = FeederModel(container=cim.Feeder(), connection=xml_file)

    # Summary
    print("CIM classes loaded:")
    for cls, objs in sorted(network.graph.items(), key=lambda x: x[0].__name__):
        if objs:
            print(f"  {cls.__name__:30s} {len(objs):>6}")

    # ── 2. Extract coordinates ────────────────────────────────────
    print("\nExtracting coordinates...")

    position_points = network.graph.get(cim.PositionPoint, {})

    # Collect raw (x, y) for normalisation bounds
    raw_points = []
    for _pp_id, pp in position_points.items():
        x = getattr(pp, 'xPosition', None)
        y = getattr(pp, 'yPosition', None)
        if x is not None and y is not None:
            try:
                raw_points.append((float(x), float(y)))
            except (ValueError, TypeError):
                pass

    # Normalise into ~0.1° box centred on Los Angeles
    if raw_points:
        min_x = min(p[0] for p in raw_points)
        max_x = max(p[0] for p in raw_points)
        min_y = min(p[1] for p in raw_points)
        max_y = max(p[1] for p in raw_points)
        span_x = max_x - min_x if max_x != min_x else 1
        span_y = max_y - min_y if max_y != min_y else 1

        def normalize(x, y):
            lon = (x - min_x) / span_x * 0.1 - 118.2437
            lat = (y - min_y) / span_y * 0.1 + 34.0522
            return lat, lon
    else:
        def normalize(x, y):
            return 34.0522, -118.2437

    print(f"  {len(raw_points)} position points found")

    # Map Location mRID → (lat, lon)
    location_coords: dict[str, tuple[float, float]] = {}
    for _pp_id, pp in position_points.items():
        loc = getattr(pp, 'Location', None)
        loc_id = mrid_str(loc)
        x = getattr(pp, 'xPosition', None)
        y = getattr(pp, 'yPosition', None)
        if loc_id and x is not None and y is not None:
            try:
                lat, lon = normalize(float(x), float(y))
                if loc_id not in location_coords:
                    location_coords[loc_id] = (lat, lon)
            except (ValueError, TypeError):
                pass

    print(f"  {len(location_coords)} locations mapped")

    # Equipment mRID → (lat, lon) via their Location
    eq_coords: dict[str, tuple[float, float]] = {}

    eq_classes_with_location = [
        cim.ACLineSegment, cim.PowerTransformer, cim.Breaker,
        cim.LoadBreakSwitch, cim.EnergyConsumer, cim.EnergySource,
    ]
    for optional_name in ('Fuse', 'Disconnector', 'Recloser', 'Substation'):
        cls = getattr(cim, optional_name, None)
        if cls:
            eq_classes_with_location.append(cls)

    for eq_cls in eq_classes_with_location:
        for _eid, eq in network.graph.get(eq_cls, {}).items():
            eq_m = mrid_str(eq)
            loc = getattr(eq, 'Location', None)
            loc_id = mrid_str(loc)
            if eq_m and loc_id and loc_id in location_coords:
                eq_coords[eq_m] = location_coords[loc_id]

    print(f"  {len(eq_coords)} equipment items geocoded")

    # ── 3. Build terminal connectivity ────────────────────────────
    print("\nBuilding terminal connectivity...")

    terminals = network.graph.get(cim.Terminal, {})

    # equipment mRID → [(terminal_obj, connectivity_node_mRID)]
    eq_terminals: dict[str, list] = defaultdict(list)
    # connectivity_node mRID → [equipment mRID]
    cn_equipment: dict[str, list] = defaultdict(list)

    for _tid, term in terminals.items():
        ce = getattr(term, 'ConductingEquipment', None)
        cn = getattr(term, 'ConnectivityNode', None)
        ce_m = mrid_str(ce) if ce else None
        cn_m = mrid_str(cn) if cn else None
        if ce_m and cn_m:
            eq_terminals[ce_m].append((term, cn_m))
            cn_equipment[cn_m].append(ce_m)

    print(f"  {len(terminals)} terminals → "
          f"{len(eq_terminals)} equipment → "
          f"{len(cn_equipment)} connectivity nodes")

    # ── 4. Classify equipment ─────────────────────────────────────
    equipment_types: dict[str, str] = {}
    equipment_open: dict[str, bool] = {}

    type_map: dict = {
        cim.ACLineSegment: 'ACLineSegment',
        cim.PowerTransformer: 'PowerTransformer',
        cim.Breaker: 'Breaker',
        cim.LoadBreakSwitch: 'LoadBreakSwitch',
        cim.EnergyConsumer: 'EnergyConsumer',
        cim.EnergySource: 'EnergySource',
    }
    for opt_name, type_str in [
        ('Fuse', 'Fuse'), ('Disconnector', 'Disconnector'), ('Recloser', 'Recloser')
    ]:
        cls = getattr(cim, opt_name, None)
        if cls:
            type_map[cls] = type_str

    for eq_cls, type_name in type_map.items():
        for _eid, eq in network.graph.get(eq_cls, {}).items():
            m = mrid_str(eq)
            if m:
                equipment_types[m] = type_name
                if type_name in ('Breaker', 'LoadBreakSwitch', 'Fuse', 'Disconnector', 'Recloser'):
                    is_open = getattr(eq, 'normalOpen', None) or getattr(eq, 'open', None)
                    equipment_open[m] = bool(is_open) if is_open is not None else False

    for _sid, sub in network.graph.get(cim.Substation, {}).items():
        m = mrid_str(sub)
        if m:
            equipment_types[m] = 'Substation'

    # ── 5. Build grid_nodes from ConnectivityNodes ────────────────
    print("\nBuilding grid nodes...")

    connectivity_nodes = network.graph.get(cim.ConnectivityNode, {})
    nodes_to_insert = []

    for _cn_id, cn in connectivity_nodes.items():
        cn_mrid = mrid_str(cn)
        cn_name = get_name(cn)

        node_type = 'Bus'
        lat, lon = 0.0, 0.0
        is_open = False

        for eq_mrid in cn_equipment.get(cn_mrid, []):
            # Coordinates
            if eq_mrid in eq_coords and eq_coords[eq_mrid] != (0.0, 0.0):
                lat, lon = eq_coords[eq_mrid]

            # Type (priority: Substation > Transformer > Switch > Breaker > Meter > Bus)
            eq_type = equipment_types.get(eq_mrid)
            if eq_type:
                if eq_type == 'EnergyConsumer':
                    if node_type == 'Bus':
                        node_type = 'Meter'
                elif eq_type in ('EnergySource', 'Substation'):
                    node_type = 'Substation'
                elif eq_type == 'LoadBreakSwitch':
                    if node_type in ('Bus', 'Meter'):
                        node_type = 'Switch'
                        is_open = equipment_open.get(eq_mrid, False)
                elif eq_type == 'Breaker':
                    if node_type in ('Bus', 'Meter'):
                        node_type = 'Breaker'
                        is_open = equipment_open.get(eq_mrid, False)
                elif eq_type == 'PowerTransformer':
                    if node_type in ('Bus', 'Meter', 'Switch', 'Breaker'):
                        node_type = 'Transformer'

        nodes_to_insert.append((
            cn_mrid, node_type, cn_name,
            json.dumps(['A', 'B', 'C']),
            lat, lon, int(is_open)
        ))

    # ── 6. Build grid_edges from conducting equipment ─────────────
    print("Building grid edges...")

    edge_conductor_map = {
        'ACLineSegment': 'Overhead',
        'PowerTransformer': 'PowerTransformer',
        'Breaker': 'Breaker',
        'LoadBreakSwitch': 'LoadBreakSwitch',
        'Fuse': 'Fuse',
        'Disconnector': 'Disconnector',
        'Recloser': 'Recloser',
    }

    edges_to_insert = []
    for eq_mrid, term_list in eq_terminals.items():
        eq_type = equipment_types.get(eq_mrid)
        conductor_type = edge_conductor_map.get(eq_type)
        if conductor_type and len(term_list) >= 2:
            cn1 = term_list[0][1]
            cn2 = term_list[1][1]
            edges_to_insert.append((
                eq_mrid, cn1, cn2, conductor_type,
                json.dumps(['A', 'B', 'C'])
            ))

    # ── 7. Write to SQLite ────────────────────────────────────────
    print(f"\nWriting {len(nodes_to_insert)} nodes and "
          f"{len(edges_to_insert)} edges to SQLite...")

    conn = setup_sqlite(SQLITE_PATH)

    conn.executemany(
        "INSERT INTO grid_nodes "
        "(node_id, node_type, name, phases_present, latitude, longitude, is_open) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        nodes_to_insert
    )
    conn.executemany(
        "INSERT INTO grid_edges "
        "(edge_id, from_node_id, to_node_id, conductor_type, phases) "
        "VALUES (?, ?, ?, ?, ?)",
        edges_to_insert
    )

    # Fix zero-coordinate nodes with random scatter
    zero_nodes = conn.execute(
        "SELECT node_id FROM grid_nodes WHERE latitude = 0.0 AND longitude = 0.0"
    ).fetchall()
    if zero_nodes:
        print(f"Scattering {len(zero_nodes)} nodes with missing coordinates...")
        for (nid,) in zero_nodes:
            lat = 34.0522 + (random.random() * 0.1 - 0.05)
            lon = -118.2437 + (random.random() * 0.1 - 0.05)
            conn.execute(
                "UPDATE grid_nodes SET latitude=?, longitude=? WHERE node_id=?",
                (lat, lon, nid)
            )

    conn.commit()

    # ── Summary ───────────────────────────────────────────────────
    node_count = conn.execute("SELECT COUNT(*) FROM grid_nodes").fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM grid_edges").fetchone()[0]
    type_summary = conn.execute(
        "SELECT node_type, COUNT(*) FROM grid_nodes GROUP BY node_type ORDER BY COUNT(*) DESC"
    ).fetchall()

    print(f"\n{'=' * 50}")
    print("Ingestion complete!")
    print(f"  Nodes : {node_count}")
    print(f"  Edges : {edge_count}")
    print("  Types :")
    for t, c in type_summary:
        print(f"    {t:20s} {c}")
    print(f"  DB    : {SQLITE_PATH}")
    print(f"{'=' * 50}")

    conn.close()


if __name__ == '__main__':
    main()
