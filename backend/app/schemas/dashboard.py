from pydantic import BaseModel, ConfigDict
from typing import Any
from datetime import datetime


class IncidentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    incident_id: str
    incident_type: str
    material_id: str | None = None
    severity: str
    status: str
    created_at: datetime | None = None


class DashboardResponse(BaseModel):
    active_incidents_count: int
    critical_risk_count: int
    pending_approvals_count: int
    production_at_risk: list[str]
    recent_incidents: list[IncidentBrief]
