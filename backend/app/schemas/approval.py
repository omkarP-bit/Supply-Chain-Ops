from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: str
    incident_id: str
    plan_id: str | None = None
    requested_amount: Decimal
    approval_threshold: Decimal
    production_impact: str | None = None
    risk_if_rejected: str | None = None
    alternatives_considered: list | None = None
    requested_at: datetime
    status: str
    approved_by: str | None = None
    decision_at: datetime | None = None
    decision_reason: str | None = None


class ApprovalDecision(BaseModel):
    decision: str
    reason: str = ""
