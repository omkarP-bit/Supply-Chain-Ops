from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentCreate(BaseModel):
    incident_type: str
    material_id: str | None = None
    po_id: str | None = None
    supplier_id: str | None = None
    description: str | None = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    incident_type: str
    material_id: str | None = None
    po_id: str | None = None
    supplier_id: str | None = None
    description: str | None = None
    severity: str
    status: str
    workflow_state: dict | None = None
    created_at: datetime
    updated_at: datetime
    recovery_plans: list = []
    approval_requests: list = []


class IncidentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    incident_type: str
    material_id: str | None = None
    status: str
    severity: str
    created_at: datetime
