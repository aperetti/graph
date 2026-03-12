"""Alarm entities."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Alarm(BaseModel):
    """Represents a Meter Alarm."""
    alarm_id: str = Field(..., description="Unique identifier for the alarm")
    node_id: str = Field(..., description="ID of the meter or device associated with the alarm")
    timestamp: datetime = Field(..., description="When the alarm occurred")
    alarm_code: str = Field(..., description="Code representing the alarm type (e.g., 'OV_VOLT')")
    severity: str = Field(..., description="Severity level: INFO, WARNING, CRITICAL")
    message: Optional[str] = Field(None, description="Detailed alarm message")
    is_active: bool = Field(True, description="Whether the alarm is currently active")
