from datetime import datetime
from typing import Any, List, Optional
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


class CurrentRiskMetrics(BaseModel):
    usable_stock: float = 0.0
    safety_stock: float = 0.0
    coverage_days: float = 0.0
    consumption_30d: float = 0.0
    consumption_7d: float = 0.0
    trend: str = "STABLE"
    hours_to_stop: float = 0.0
    discrepancy_percentage: float = 0.0
    risk_severity: str = "MEDIUM"


class DoNothingImpact(BaseModel):
    hours_to_stockout: float = 0.0
    expected_shortage_units: float = 0.0
    affected_orders_count: int = 0
    line_stoppage_risk: str = "HIGH"
    summary: str = ""


class RecommendedPlanDossier(BaseModel):
    plan_id: str
    plan_name: str
    plan_type: str
    supplier_name: str
    supplier_id: str
    estimated_cost: float
    estimated_delivery_days: int
    production_impact_hours: float
    remaining_risk: str = "LOW"
    overall_score: float = 0.0
    status: str = "PROPOSED"
    rationale: str = ""
    reliability_rationale: str = ""
    budget_impact_analysis: str = ""
    why_this_plan: list[str] = []
    simulation: dict[str, Any] = {}
    allocations: list[dict[str, Any]] = []


class SupplierOptionDossier(BaseModel):
    supplier_id: str
    supplier_name: str
    unit_price: float
    lead_time_days: int
    quality_score: float
    reliability_score: float
    available_quantity: float
    certification_valid: bool
    aql_level: str = "II"
    score: float = 0.0
    is_selected: bool = False
    rejection_reason: Optional[str] = None


class DecisionTimelineItem(BaseModel):
    timestamp: datetime | None = None
    stage: str
    action: str
    outcome: str
    status: str = "COMPLETED"


class IncidentDossierResponse(BaseModel):
    incident_id: str
    incident_type: str
    material_id: str
    material_name: Optional[str] = None
    po_id: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    description: Optional[str] = None
    severity: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    workflow_stage: str = "DETECT"
    current_risk: CurrentRiskMetrics
    do_nothing_impact: DoNothingImpact
    recommended_plan: Optional[RecommendedPlanDossier] = None
    all_plans: list[RecommendedPlanDossier] = []
    supplier_comparison: list[SupplierOptionDossier] = []
    approval_request: Optional[dict[str, Any]] = None
    decision_timeline: list[DecisionTimelineItem] = []
    verification: Optional[dict[str, Any]] = None
    demo_flow_steps: list[dict[str, Any]] = []
    mvp_features: Optional[dict[str, Any]] = None
