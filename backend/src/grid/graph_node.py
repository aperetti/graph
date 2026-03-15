"""Graph node model for traversal."""
from typing import List, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Represents a node in the graph engine.

    Built from the in-memory CIM-Graph model at startup.  The
    ``connected_equipment`` list lets callers drill into the full CIM
    detail via ``CimModelManager.get_equipment_detail(mrid)``.
    """
    id: str = Field(..., description="Unique node ID (ConnectivityNode mRID)")
    type: str = Field(..., description="Derived node type (Substation, Transformer, Meter, …)")
    name: str = Field("Unknown", description="CIM IdentifiedObject.name")
    phases: List[str] = Field(
        default_factory=lambda: ["A", "B", "C"],
        description="Phase codes extracted from CIM (e.g. ['A','B','C'])",
    )
    children: List[str] = Field(default_factory=list, description="Downstream node IDs")
    parents: List[str] = Field(default_factory=list, description="Upstream node IDs")
    latitude: Optional[float] = Field(None, description="Latitude for spatial stitching")
    longitude: Optional[float] = Field(None, description="Longitude for spatial stitching")
    connected_equipment: List[str] = Field(
        default_factory=list,
        description="mRIDs of CIM equipment connected at this connectivity node",
    )
    base_voltage_kv: Optional[float] = Field(
        None, description="Nominal voltage (kV) from VoltageLevel / BaseVoltage",
    )
    transformer_kva: Optional[float] = Field(
        None, description="Nominal transformer kVA rating (for Transformer nodes)",
    )
