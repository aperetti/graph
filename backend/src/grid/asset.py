"""Base assets for the grid model."""
from typing import Optional, List
from pydantic import BaseModel, Field

class Asset(BaseModel):
    """Represents a physical electrical asset in the grid."""
    id: str = Field(..., description="Unique identifier for the asset")
    asset_type: str = Field(..., description="Type of asset (e.g., 'SubstationBreaker', 'Transformer', 'Fuse')")
    name: Optional[str] = Field(None, description="Human-readable name or label")
    phases_present: List[str] = Field(default_factory=lambda: ["A", "B", "C"], description="Phases available at this asset")

class Edge(BaseModel):
    """Represents the connectivity (conductors) between two assets."""
    id: str = Field(..., description="Unique identifier for the edge/conductor")
    from_node_id: str = Field(..., description="Source node ID")
    to_node_id: str = Field(..., description="Destination node ID")
    conductor_type: Optional[str] = Field(None, description="Wire type or characteristics")
    phases: List[str] = Field(default_factory=lambda: ["A", "B", "C"], description="Energized phases taking this path")
