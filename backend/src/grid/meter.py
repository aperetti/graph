"""Meter entities."""
from typing import Optional
from pydantic import BaseModel, Field

class Meter(BaseModel):
    """Represents an AMI Meter."""
    id: str = Field(..., description="Unique identifier for the meter")
    name: Optional[str] = Field(None, description="Human-readable name or label")
    phases_present: str = Field(..., description="Phases available at this meter (e.g., 'A', 'B', 'C', 'ABC')")
    service_point_id: Optional[str] = Field(None, description="Associated service point identifier")
