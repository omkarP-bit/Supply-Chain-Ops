from pydantic import BaseModel, ConfigDict
from typing import Any
from datetime import datetime


class CriticalIncidentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    incident_id: str
    po_id: str | None = None
    material_id: str
    material_name: str | None = None
    incident_type: str
    severity: str
    production_impact_hours: float = 0.0
    coverage_days: float = 0.0
    status: str
    approval_status: str = "NOT_REQUIRED"
    created_at: datetime | None = None


class ProductionRiskItem(BaseModel):
    material_id: str
    material_name: str
    usable_stock: float
    safety_stock: float
    coverage_days: float
    hours_to_stop: float
    affected_orders_count: int
    risk_level: str


class PendingApprovalItem(BaseModel):
    approval_id: str
    incident_id: str
    plan_id: str
    supplier_name: str
    material_id: str
    requested_amount: float
    lead_time_days: int = 0
    production_impact_hours: float = 0.0
    risk_level: str = "MEDIUM"
    recommendation_reason: str = ""
    status: str = "PENDING"
    created_at: datetime | None = None


class DashboardResponse(BaseModel):
    active_incidents_count: int
    critical_risk_count: int
    pending_approvals_count: int
    components_at_risk_count: int
    critical_incidents: list[CriticalIncidentItem] = []
    production_at_risk: list[ProductionRiskItem] = []
    pending_approvals: list[PendingApprovalItem] = []
    status_summary: dict[str, int] = {}
    recent_incidents: list[Any] = []
