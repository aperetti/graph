"""Time-series reading entities."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class Reading(BaseModel):
    """Represents a time-series interval reading from a meter."""
    model_config = ConfigDict(populate_by_name=True)

    node_id: str = Field(..., description="The meter or device ID")
    timestamp: datetime = Field(..., description="The interval start/end time")
    
    # Energy
    kwh_dlv: Optional[float] = Field(None, description="Energy Delivered (kWh)")
    kwh_rcv: Optional[float] = Field(None, description="Energy Received (kWh)")
    kvarh_dlv: Optional[float] = Field(None, description="Reactive Energy Delivered (kVARh)")
    kvarh_rcv: Optional[float] = Field(None, description="Reactive Energy Received (kVARh)")
    
    # Power Quality (Instantaneous)
    voltage_a: Optional[float] = Field(None, description="Instantaneous Voltage Phase A")
    voltage_b: Optional[float] = Field(None, description="Instantaneous Voltage Phase B")
    voltage_c: Optional[float] = Field(None, description="Instantaneous Voltage Phase C")
    
    current_a: Optional[float] = Field(None, description="Instantaneous Current Phase A")
    current_b: Optional[float] = Field(None, description="Instantaneous Current Phase B")
    current_c: Optional[float] = Field(None, description="Instantaneous Current Phase C")
    
    power_factor: Optional[float] = Field(None, description="Power Factor")
