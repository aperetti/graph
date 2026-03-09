"""Graph node model for traversal."""
from typing import List, Optional
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    """Represents a node in the graph engine."""
    id: str = Field(..., description="Unique node ID")
    type: str = Field(..., description="Type of the node (asset type)")
    phases: List[str] = Field(default_factory=lambda: ["A", "B", "C"], description="Phases available at this node")
    children: List[str] = Field(default_factory=list, description="Downstream node IDs")
    parents: List[str] = Field(default_factory=list, description="Upstream node IDs")
    latitude: Optional[float] = Field(None, description="Latitude for spatial stitching")
    longitude: Optional[float] = Field(None, description="Longitude for spatial stitching")
