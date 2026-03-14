"""CIM-Graph Model Manager – singleton that holds the FeederModel in memory.

The entire CIM XML is parsed once at application startup via PNNL CIM-Graph.
All topology queries, equipment look-ups and graph construction are served
from the in-memory model rather than from SQLite / DuckDB.

Usage:
    from src.shared.cim_model import CimModelManager

    manager = CimModelManager.get_instance()
    manager.load()                          # called once at startup
    nodes  = manager.get_topology_nodes()   # replaces SQLite reads
    detail = manager.get_equipment_detail("some-mrid")
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
_SHARED_DIR = Path(__file__).resolve().parent          # backend/src/shared/
_BACKEND_DIR = _SHARED_DIR.parents[1]                  # backend/
_WORKSPACE_ROOT = _BACKEND_DIR.parent                  # project root

# CIM-Graph environment (must be set before importing cimgraph)
os.environ.setdefault("CIMG_CIM_PROFILE", "rc4_2021")
os.environ.setdefault("CIMG_IEC61970_301", "8")


def _resolve_xml_path() -> Path:
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
        _BACKEND_DIR / "sample_data" / "IEEE8500_3subs.xml",
        _BACKEND_DIR / "sample_data" / "IEEE8500.xml",
        _WORKSPACE_ROOT / "backend" / "sample_data" / "IEEE8500.xml",
    ]
    for c in candidates:
        if c.is_file():
            return c

    return _BACKEND_DIR / "sample_data" / "IEEE8500.xml"


# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------

def _mrid_str(obj) -> Optional[str]:
    if obj is None:
        return None
    m = getattr(obj, "mRID", None)
    if m is None:
        return None
    s = str(m)
    for prefix in ("urn:uuid:", "_"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def _get_name(obj) -> str:
    name = getattr(obj, "name", None)
    return name if name else (_mrid_str(obj) or "Unknown")


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_phase_code(phase_code) -> Optional[list[str]]:
    """Convert CIM PhaseCode enum to list of phase strings."""
    if phase_code is None:
        return None
    pc_str = str(phase_code)
    # Handle enum-style: PhaseCode.ABC, PhaseCode.A, etc.
    if "." in pc_str:
        pc_str = pc_str.split(".")[-1]
    if pc_str in ("none", "None", "NONE", ""):
        return None
    # Split-phase handling
    if "s" in pc_str.lower():
        phases = []
        if "s1" in pc_str.lower():
            phases.append("S1")
        if "s2" in pc_str.lower():
            phases.append("S2")
        for c in pc_str.upper():
            if c in ("A", "B", "C", "N") and c not in phases:
                phases.append(c)
        return phases if phases else None
    # Standard phases
    phases = [c for c in pc_str.upper() if c in ("A", "B", "C", "N")]
    return phases if phases else None


# ═══════════════════════════════════════════════════════════════════════════
# CimModelManager
# ═══════════════════════════════════════════════════════════════════════════

class CimModelManager:
    """Singleton that owns the in-memory CIM-Graph FeederModel.

    After ``load()`` is called the manager provides:
    * Pre-computed topology (nodes & edges) for the NetworkX graph.
    * Rich CIM equipment look-ups by mRID or CIM class.
    * Container / voltage-level hierarchy queries.
    """

    _instance: Optional["CimModelManager"] = None

    def __init__(self):
        self.network = None          # FeederModel
        self.cim = None              # cimgraph.data_profile.rc4_2021
        self._loaded = False

        # ── Indexes (populated by _build_indexes) ─────────────────
        self._equipment_index: dict[str, tuple[str, Any]] = {}   # mRID → (cls_name, obj)
        self._equipment_types: dict[str, str] = {}               # mRID → type label
        self._equipment_open: dict[str, bool] = {}               # mRID → open state
        self._eq_coords: dict[str, tuple[float, float]] = {}    # mRID → (lat, lon)
        self._location_coords: dict[str, tuple[float, float]] = {}
        self._eq_terminals: dict[str, list] = defaultdict(list)  # eq mRID → [(term, cn_mRID)]
        self._cn_equipment: dict[str, list] = defaultdict(list)  # cn mRID → [eq mRID]
        self._eq_phases: dict[str, list[str]] = {}               # eq mRID → ["A","B",…]

        # ── Pre-computed topology ─────────────────────────────────
        self._topology_nodes: list[dict] = []
        self._topology_edges: list[dict] = []

    # ── Singleton access ──────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "CimModelManager":
        if cls._instance is None:
            cls._instance = CimModelManager()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (useful for testing)."""
        cls._instance = None

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ══════════════════════════════════════════════════════════════
    # Loading
    # ══════════════════════════════════════════════════════════════

    def load(self, xml_path: str | None = None):
        """Parse the CIM XML with CIM-Graph and build all indexes.

        Safe to call multiple times – subsequent calls are no-ops.
        """
        if self._loaded:
            logger.info("CIM model already loaded – skipping")
            return

        path = Path(xml_path) if xml_path else _resolve_xml_path()
        logger.info("Loading CIM model from: %s", path)

        if not path.is_file():
            raise FileNotFoundError(f"CIM XML not found: {path}")

        # ── Import CIM-Graph (deferred so env vars are set first) ─
        import cimgraph.data_profile.rc4_2021 as cim
        from cimgraph.databases import XMLFile
        from cimgraph.models import FeederModel

        self.cim = cim

        xml_file = XMLFile(filename=str(path))
        self.network = FeederModel(container=cim.Feeder(), connection=xml_file)

        logger.info("CIM classes loaded:")
        for cls, objs in sorted(self.network.graph.items(), key=lambda x: x[0].__name__):
            if objs:
                logger.info("  %-30s %6d", cls.__name__, len(objs))

        self._build_indexes()
        self._loaded = True
        logger.info(
            "CIM model ready – %d nodes, %d edges",
            len(self._topology_nodes),
            len(self._topology_edges),
        )

    # ══════════════════════════════════════════════════════════════
    # Index construction (private)
    # ══════════════════════════════════════════════════════════════

    def _build_indexes(self):
        cim = self.cim
        graph = self.network.graph

        # ── 1. Equipment master index ─────────────────────────────
        for cim_cls, objs in graph.items():
            cls_name = cim_cls.__name__
            for _eid, obj in objs.items():
                m = _mrid_str(obj)
                if m:
                    self._equipment_index[m] = (cls_name, obj)

        # ── 2. Coordinates ────────────────────────────────────────
        self._build_coordinate_index()

        # ── 3. Terminal connectivity ──────────────────────────────
        terminals = graph.get(cim.Terminal, {})
        for _tid, term in terminals.items():
            ce = getattr(term, "ConductingEquipment", None)
            cn = getattr(term, "ConnectivityNode", None)
            ce_m = _mrid_str(ce) if ce else None
            cn_m = _mrid_str(cn) if cn else None
            if ce_m and cn_m:
                self._eq_terminals[ce_m].append((term, cn_m))
                self._cn_equipment[cn_m].append(ce_m)

        logger.info(
            "  %d terminals → %d equipment → %d connectivity nodes",
            len(terminals),
            len(self._eq_terminals),
            len(self._cn_equipment),
        )

        # ── 4. Classify equipment ─────────────────────────────────
        self._classify_equipment()

        # ── 5. Equipment phase index from per-phase CIM objects ───
        self._build_equipment_phase_index()

        # ── 6. Build topology graph ───────────────────────────────
        self._build_topology()

    # ── Coordinates ───────────────────────────────────────────────

    def _build_coordinate_index(self):
        cim = self.cim
        graph = self.network.graph

        position_points = graph.get(cim.PositionPoint, {})
        raw_points: list[tuple[float, float]] = []

        for _pp_id, pp in position_points.items():
            x = _safe_float(getattr(pp, "xPosition", None))
            y = _safe_float(getattr(pp, "yPosition", None))
            if x is not None and y is not None:
                raw_points.append((x, y))

        # Normalise into ~0.1° box centred on Los Angeles
        if raw_points:
            min_x = min(p[0] for p in raw_points)
            max_x = max(p[0] for p in raw_points)
            min_y = min(p[1] for p in raw_points)
            max_y = max(p[1] for p in raw_points)
            span_x = (max_x - min_x) or 1.0
            span_y = (max_y - min_y) or 1.0

            def _normalize(x, y):
                lon = (x - min_x) / span_x * 0.1 - 118.2437
                lat = (y - min_y) / span_y * 0.1 + 34.0522
                return lat, lon
        else:
            def _normalize(x, y):
                return 34.0522, -118.2437

        # Location mRID → (lat, lon)
        for _pp_id, pp in position_points.items():
            loc = getattr(pp, "Location", None)
            loc_id = _mrid_str(loc)
            x = _safe_float(getattr(pp, "xPosition", None))
            y = _safe_float(getattr(pp, "yPosition", None))
            if loc_id and x is not None and y is not None:
                if loc_id not in self._location_coords:
                    self._location_coords[loc_id] = _normalize(x, y)

        # Equipment mRID → (lat, lon)
        eq_cls_with_location = [
            cim.ACLineSegment, cim.PowerTransformer, cim.Breaker,
            cim.LoadBreakSwitch, cim.EnergyConsumer, cim.EnergySource,
        ]
        for opt in ("Fuse", "Disconnector", "Recloser", "Substation",
                     "LinearShuntCompensator"):
            cls = getattr(cim, opt, None)
            if cls:
                eq_cls_with_location.append(cls)

        for eq_cls in eq_cls_with_location:
            for _eid, eq in graph.get(eq_cls, {}).items():
                eq_m = _mrid_str(eq)
                loc = getattr(eq, "Location", None)
                loc_id = _mrid_str(loc)
                if eq_m and loc_id and loc_id in self._location_coords:
                    self._eq_coords[eq_m] = self._location_coords[loc_id]

        logger.info(
            "  %d position points → %d locations → %d equipment geocoded",
            len(raw_points),
            len(self._location_coords),
            len(self._eq_coords),
        )

    # ── Equipment classification ──────────────────────────────────

    def _classify_equipment(self):
        cim = self.cim
        graph = self.network.graph

        type_map: dict = {
            cim.ACLineSegment: "ACLineSegment",
            cim.PowerTransformer: "PowerTransformer",
            cim.Breaker: "Breaker",
            cim.LoadBreakSwitch: "LoadBreakSwitch",
            cim.EnergyConsumer: "EnergyConsumer",
            cim.EnergySource: "EnergySource",
        }
        for opt_name, type_str in [
            ("Fuse", "Fuse"),
            ("Disconnector", "Disconnector"),
            ("Recloser", "Recloser"),
            ("LinearShuntCompensator", "Capacitor"),
        ]:
            cls = getattr(cim, opt_name, None)
            if cls:
                type_map[cls] = type_str

        for eq_cls, type_name in type_map.items():
            for _eid, eq in graph.get(eq_cls, {}).items():
                m = _mrid_str(eq)
                if m:
                    self._equipment_types[m] = type_name
                    if type_name in ("Breaker", "LoadBreakSwitch", "Fuse",
                                     "Disconnector", "Recloser"):
                        is_open = getattr(eq, "normalOpen", None) or getattr(eq, "open", None)
                        self._equipment_open[m] = bool(is_open) if is_open is not None else False

        for _sid, sub in graph.get(cim.Substation, {}).items():
            m = _mrid_str(sub)
            if m:
                self._equipment_types[m] = "Substation"

    # ── Equipment phase index ─────────────────────────────────────

    def _build_equipment_phase_index(self):
        """Build eq mRID → phase list from per-phase CIM objects.

        CIM stores phases on dedicated association objects rather than on
        Terminal.phases (which is often unpopulated).  We scan:
        * ACLineSegmentPhase   → ACLineSegment
        * EnergyConsumerPhase  → EnergyConsumer
        * SwitchPhase          → Switch (Breaker / LoadBreakSwitch etc.)
        * ShuntCompensatorPhase→ ShuntCompensator
        """
        cim = self.cim
        graph = self.network.graph

        # (phase_class, parent_attr_name)
        phase_class_map: list[tuple] = []

        for cls_name, parent_attr in [
            ("ACLineSegmentPhase",    "ACLineSegment"),
            ("EnergyConsumerPhase",   "EnergyConsumer"),
            ("SwitchPhase",           "Switch"),
            ("ShuntCompensatorPhase", "ShuntCompensator"),
        ]:
            cls = getattr(cim, cls_name, None)
            if cls and graph.get(cls):
                phase_class_map.append((cls, parent_attr))

        for phase_cls, parent_attr in phase_class_map:
            for _pid, ph_obj in graph.get(phase_cls, {}).items():
                parent = getattr(ph_obj, parent_attr, None)
                parent_id = _mrid_str(parent)
                if not parent_id:
                    continue
                pc = getattr(ph_obj, "phase", None)
                if pc is None:
                    continue
                parsed = _parse_phase_code(pc)
                if parsed:
                    existing = self._eq_phases.setdefault(parent_id, [])
                    for p in parsed:
                        if p not in existing:
                            existing.append(p)

        # Sort each phase list into a canonical order
        _phase_order = {"A": 0, "B": 1, "C": 2, "N": 3, "S1": 4, "S2": 5}
        for eq_mrid, phases in self._eq_phases.items():
            phases.sort(key=lambda p: _phase_order.get(p, 9))

        logger.info(
            "  Equipment phase index: %d equipment with per-phase data",
            len(self._eq_phases),
        )

    # ── Topology graph ────────────────────────────────────────────

    def _build_topology(self):
        """Build grid_nodes and grid_edges from ConnectivityNodes & equipment."""
        cim = self.cim
        graph = self.network.graph

        # ── Nodes from ConnectivityNodes ──────────────────────────
        connectivity_nodes = graph.get(cim.ConnectivityNode, {})

        for _cn_id, cn in connectivity_nodes.items():
            cn_mrid = _mrid_str(cn)
            cn_name = _get_name(cn)

            node_type = "Bus"
            lat, lon = 0.0, 0.0
            is_open = False
            connected_equipment: list[str] = []

            for eq_mrid in self._cn_equipment.get(cn_mrid, []):
                connected_equipment.append(eq_mrid)

                # Coordinates
                if eq_mrid in self._eq_coords and self._eq_coords[eq_mrid] != (0.0, 0.0):
                    lat, lon = self._eq_coords[eq_mrid]

                eq_type = self._equipment_types.get(eq_mrid)
                if eq_type:
                    if eq_type == "EnergyConsumer":
                        if node_type == "Bus":
                            node_type = "Meter"
                    elif eq_type in ("EnergySource", "Substation"):
                        node_type = "Substation"
                    elif eq_type == "LoadBreakSwitch":
                        if node_type in ("Bus", "Meter"):
                            node_type = "Switch"
                            is_open = self._equipment_open.get(eq_mrid, False)
                    elif eq_type == "Breaker":
                        if node_type in ("Bus", "Meter"):
                            node_type = "Breaker"
                            is_open = self._equipment_open.get(eq_mrid, False)
                    elif eq_type == "PowerTransformer":
                        if node_type in ("Bus", "Meter", "Switch", "Breaker"):
                            node_type = "Transformer"
                    elif eq_type == "Capacitor":
                        if node_type == "Bus":
                            node_type = "Capacitor"

            # Actual phase codes from CIM
            phases = self._get_phases_for_cn(cn_mrid) or ["A", "B", "C"]

            # Scatter zero-coordinate nodes
            if lat == 0.0 and lon == 0.0:
                lat = 34.0522 + (random.random() * 0.1 - 0.05)
                lon = -118.2437 + (random.random() * 0.1 - 0.05)

            # Base-voltage from VoltageLevel container
            base_voltage_kv = None
            container = getattr(cn, "ConnectivityNodeContainer", None)
            if container:
                bv = getattr(container, "BaseVoltage", None)
                if bv:
                    base_voltage_kv = _safe_float(getattr(bv, "nominalVoltage", None))

            self._topology_nodes.append({
                "node_id": cn_mrid,
                "node_type": node_type,
                "name": cn_name,
                "phases_present": phases,
                "latitude": lat,
                "longitude": lon,
                "is_open": is_open,
                "connected_equipment": connected_equipment,
                "base_voltage_kv": base_voltage_kv,
            })

        # ── Edges from conducting equipment ───────────────────────
        edge_conductor_map = {
            "ACLineSegment": "Overhead",
            "PowerTransformer": "PowerTransformer",
            "Breaker": "Breaker",
            "LoadBreakSwitch": "LoadBreakSwitch",
            "Fuse": "Fuse",
            "Disconnector": "Disconnector",
            "Recloser": "Recloser",
            "Capacitor": "Capacitor",
        }

        for eq_mrid, term_list in self._eq_terminals.items():
            eq_type = self._equipment_types.get(eq_mrid)
            conductor_type = edge_conductor_map.get(eq_type)
            if conductor_type and len(term_list) >= 2:
                cn1 = term_list[0][1]
                cn2 = term_list[1][1]
                phases = self._get_phases_for_equipment(eq_mrid) or ["A", "B", "C"]

                self._topology_edges.append({
                    "edge_id": eq_mrid,
                    "from_node_id": cn1,
                    "to_node_id": cn2,
                    "conductor_type": conductor_type,
                    "phases": phases,
                })

        logger.info(
            "Topology built: %d nodes, %d edges",
            len(self._topology_nodes),
            len(self._topology_edges),
        )

    # ── Phase helpers ─────────────────────────────────────────────

    def _get_phases_for_cn(self, cn_mrid: str) -> list[str] | None:
        for eq_mrid in self._cn_equipment.get(cn_mrid, []):
            phases = self._get_phases_for_equipment(eq_mrid)
            if phases:
                return phases
        return None

    def _get_phases_for_equipment(self, eq_mrid: str) -> list[str] | None:
        # 1. Per-phase CIM objects (ACLineSegmentPhase etc.) – most reliable
        if eq_mrid in self._eq_phases:
            return self._eq_phases[eq_mrid]

        # 2. Terminal.phases (populated in some profiles / models)
        for term, _ in self._eq_terminals.get(eq_mrid, []):
            phase_code = getattr(term, "phases", None)
            if phase_code:
                parsed = _parse_phase_code(phase_code)
                if parsed:
                    return parsed
        return None

    # ══════════════════════════════════════════════════════════════
    # Public query API
    # ══════════════════════════════════════════════════════════════

    def get_topology_nodes(self) -> list[dict]:
        """All pre-computed topology nodes (same shape as SqliteRepository)."""
        return self._topology_nodes

    def get_topology_edges(self) -> list[dict]:
        """All pre-computed topology edges."""
        return self._topology_edges

    def get_cim_classes(self) -> dict[str, int]:
        """Summary of every CIM class in the model with object counts."""
        result = {}
        for cls, objs in self.network.graph.items():
            if objs:
                result[cls.__name__] = len(objs)
        return dict(sorted(result.items()))

    def get_all_equipment_by_class(self, class_name: str) -> list[dict]:
        """Return summary dicts for every object of a given CIM class."""
        results = []
        for cim_cls, objs in self.network.graph.items():
            if cim_cls.__name__ == class_name:
                for _eid, obj in objs.items():
                    m = _mrid_str(obj)
                    if m:
                        results.append({
                            "mrid": m,
                            "name": _get_name(obj),
                            "cim_class": class_name,
                        })
        return results

    # ── Equipment detail ──────────────────────────────────────────

    def get_equipment_detail(self, mrid: str) -> dict | None:
        """Full CIM detail for any equipment by mRID."""
        entry = self._equipment_index.get(mrid)
        if not entry:
            return None

        cls_name, obj = entry
        detail: dict[str, Any] = {
            "mrid": mrid,
            "cim_class": cls_name,
            "name": _get_name(obj),
        }

        # Common optional attributes
        for attr in ("description", "aliasName"):
            val = getattr(obj, attr, None)
            if val:
                detail[attr] = str(val)

        # Coordinates
        if mrid in self._eq_coords:
            detail["latitude"], detail["longitude"] = self._eq_coords[mrid]

        # BaseVoltage (directly on equipment)
        bv = getattr(obj, "BaseVoltage", None)
        if bv:
            detail["base_voltage_kv"] = _safe_float(getattr(bv, "nominalVoltage", None))

        # Container hierarchy
        container = getattr(obj, "EquipmentContainer", None)
        if container:
            detail["container"] = {
                "mrid": _mrid_str(container),
                "name": _get_name(container),
                "class": type(container).__name__,
            }

        # Terminals / connectivity
        terms = self._eq_terminals.get(mrid, [])
        detail["terminals"] = [
            {
                "connectivity_node": cn_m,
                "phases": _parse_phase_code(getattr(t, "phases", None)),
            }
            for t, cn_m in terms
        ]

        # Type-specific enrichment
        enrichers = {
            "ACLineSegment": self._enrich_line_segment,
            "PowerTransformer": self._enrich_transformer,
            "Breaker": self._enrich_switch,
            "LoadBreakSwitch": self._enrich_switch,
            "Fuse": self._enrich_switch,
            "Disconnector": self._enrich_switch,
            "Recloser": self._enrich_switch,
            "EnergyConsumer": self._enrich_energy_consumer,
            "EnergySource": self._enrich_energy_source,
            "LinearShuntCompensator": self._enrich_capacitor,
        }
        enricher = enrichers.get(cls_name)
        if enricher:
            enricher(detail, obj)

        return detail

    def get_node_cim_details(self, node_id: str) -> dict | None:
        """Enriched CIM details for a connectivity-node and its equipment."""
        cim = self.cim
        cn_obj = None
        for _cid, cn in self.network.graph.get(cim.ConnectivityNode, {}).items():
            if _mrid_str(cn) == node_id:
                cn_obj = cn
                break

        if cn_obj is None:
            return None

        result: dict[str, Any] = {
            "node_id": node_id,
            "name": _get_name(cn_obj),
            "connected_equipment": [],
        }

        # Container / VoltageLevel
        container = getattr(cn_obj, "ConnectivityNodeContainer", None)
        if container:
            result["container"] = {
                "mrid": _mrid_str(container),
                "name": _get_name(container),
                "class": type(container).__name__,
            }
            bv = getattr(container, "BaseVoltage", None)
            if bv:
                result["base_voltage_kv"] = _safe_float(
                    getattr(bv, "nominalVoltage", None)
                )

        # All connected equipment with full details
        for eq_mrid in self._cn_equipment.get(node_id, []):
            eq_detail = self.get_equipment_detail(eq_mrid)
            if eq_detail:
                result["connected_equipment"].append(eq_detail)

        return result

    # ── Type-specific enrichment helpers ──────────────────────────

    def _enrich_line_segment(self, detail: dict, obj):
        """ACLineSegment: impedance, length, conductor info."""
        for attr, key in [
            ("length", "length_m"),
            ("r", "resistance_ohm"),
            ("x", "reactance_ohm"),
            ("r0", "zero_seq_resistance_ohm"),
            ("x0", "zero_seq_reactance_ohm"),
            ("bch", "susceptance_S"),
            ("gch", "conductance_S"),
            ("ratedCurrent", "rated_current_a"),
        ]:
            val = _safe_float(getattr(obj, attr, None))
            if val is not None:
                detail[key] = val

        pli = getattr(obj, "PerLengthImpedance", None)
        if pli:
            detail["per_length_impedance"] = {
                "mrid": _mrid_str(pli),
                "name": _get_name(pli),
            }

    def _enrich_transformer(self, detail: dict, obj):
        """PowerTransformer: winding data, tap changer."""
        cim = self.cim

        # Collect PowerTransformerEnd windings
        ends: list[dict] = []
        pte_cls = getattr(cim, "PowerTransformerEnd", None)
        if pte_cls:
            for _eid, pte in self.network.graph.get(pte_cls, {}).items():
                pt = getattr(pte, "PowerTransformer", None)
                if pt and _mrid_str(pt) == detail["mrid"]:
                    end_data: dict[str, Any] = {
                        "mrid": _mrid_str(pte),
                        "name": _get_name(pte),
                        "end_number": getattr(pte, "endNumber", None),
                    }
                    for attr, key in [
                        ("ratedS", "rated_kva"),
                        ("ratedU", "rated_kv"),
                        ("r", "resistance_ohm"),
                        ("x", "reactance_ohm"),
                        ("connectionKind", "connection_kind"),
                    ]:
                        val = getattr(pte, attr, None)
                        if val is not None:
                            if attr == "connectionKind":
                                end_data[key] = str(val)
                            else:
                                fv = _safe_float(val)
                                if fv is not None:
                                    end_data[key] = fv
                    ends.append(end_data)

        detail["windings"] = sorted(ends, key=lambda e: e.get("end_number") or 0)

        # Tap changer
        rtc_cls = getattr(cim, "RatioTapChanger", None)
        if rtc_cls:
            winding_mrids = {w["mrid"] for w in ends if w.get("mrid")}
            for _rid, rtc in self.network.graph.get(rtc_cls, {}).items():
                te = getattr(rtc, "TransformerEnd", None)
                if te and _mrid_str(te) in winding_mrids:
                    detail["tap_changer"] = {
                        "mrid": _mrid_str(rtc),
                        "step": getattr(rtc, "step", None),
                        "high_step": getattr(rtc, "highStep", None),
                        "low_step": getattr(rtc, "lowStep", None),
                        "neutral_step": getattr(rtc, "neutralStep", None),
                        "step_voltage_increment": _safe_float(
                            getattr(rtc, "stepVoltageIncrement", None)
                        ),
                    }
                    break

    def _enrich_switch(self, detail: dict, obj):
        """Breaker / LoadBreakSwitch / Fuse / Disconnector / Recloser."""
        detail["normal_open"] = bool(getattr(obj, "normalOpen", False))
        detail["open"] = bool(getattr(obj, "open", False))
        val = _safe_float(getattr(obj, "ratedCurrent", None))
        if val is not None:
            detail["rated_current_a"] = val
        val = _safe_float(getattr(obj, "breakingCapacity", None))
        if val is not None:
            detail["breaking_capacity"] = val

    def _enrich_energy_consumer(self, detail: dict, obj):
        """EnergyConsumer (load / meter)."""
        for attr, key in [
            ("p", "active_power_w"),
            ("q", "reactive_power_var"),
        ]:
            val = _safe_float(getattr(obj, attr, None))
            if val is not None:
                detail[key] = val

        cc = getattr(obj, "customerCount", None)
        if cc is not None:
            try:
                detail["customer_count"] = int(cc)
            except (ValueError, TypeError):
                pass

        pc = getattr(obj, "phaseConnection", None)
        if pc:
            detail["phase_connection"] = str(pc)

    def _enrich_energy_source(self, detail: dict, obj):
        """EnergySource (substation source)."""
        for attr, key in [
            ("nominalVoltage", "nominal_voltage_kv"),
            ("voltageMagnitude", "voltage_magnitude"),
            ("voltageAngle", "voltage_angle_deg"),
            ("r", "resistance_ohm"),
            ("x", "reactance_ohm"),
            ("r0", "zero_seq_resistance_ohm"),
            ("x0", "zero_seq_reactance_ohm"),
        ]:
            val = _safe_float(getattr(obj, attr, None))
            if val is not None:
                detail[key] = val

    def _enrich_capacitor(self, detail: dict, obj):
        """LinearShuntCompensator (capacitor bank)."""
        for attr, key in [
            ("bPerSection", "b_per_section_S"),
            ("gPerSection", "g_per_section_S"),
            ("nomU", "nominal_voltage_kv"),
            ("normalSections", "normal_sections"),
            ("maximumSections", "maximum_sections"),
        ]:
            val = _safe_float(getattr(obj, attr, None))
            if val is not None:
                detail[key] = val
