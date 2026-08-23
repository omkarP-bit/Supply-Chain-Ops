from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


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
    decision: str = Field(pattern="^(approve|reject)$")
    reason: str = Field(default="", max_length=512)


class ExecutionCommand(BaseModel):
    plan_id: str = Field(min_length=1, max_length=32)
    approval_id: str = Field(min_length=1, max_length=32)
