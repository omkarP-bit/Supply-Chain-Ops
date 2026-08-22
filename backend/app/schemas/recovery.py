from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan_id: str
    incident_id: str
    plan_name: str
    plan_type: str
    plan_details: dict | None = None
    estimated_cost: Decimal
    estimated_delivery_days: Decimal
    production_impact_hours: Decimal
    supplier_risk_score: Decimal
    quality_score: Decimal
    robustness_score: Decimal
    overall_score: Decimal
    status: str
    selected: bool
    created_at: datetime


class PlanCreate(BaseModel):
    incident_id: str
    plan_name: str
    plan_type: str
    plan_details: dict = {}


class RecommendationRequest(BaseModel):
    incident_id: str


class AnalysisResponse(BaseModel):
    incident_id: str
    risk_report: dict
    eligible_suppliers: list
