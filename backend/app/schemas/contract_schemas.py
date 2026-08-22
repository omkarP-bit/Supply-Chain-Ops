from datetime import datetime, date
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    component_id: str
    name: str
    current_stock: int
    usable_stock: int
    daily_usage: int
    safety_stock: int
    warehouse: str | None = None
    last_updated: datetime | None = None


class PurchaseOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    po_id: str
    component_id: str
    supplier_id: str
    quantity: int
    expected_delivery: datetime | date
    status: str
    unit_price: Decimal
    total_value: Decimal
    approval_required_above: Decimal
    version: int


class PurchaseOrderPatch(BaseModel):
    version: int
    status: str | None = None
    expected_delivery: datetime | date | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None


class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supplier_id: str
    supplier_name: str
    component_id: str | None = None
    unit_price: Decimal
    lead_time_days: int
    available_quantity: int
    quality_score: Decimal
    reliability_score: Decimal
    min_order_quantity: int
    certifications: list[str] | None = None


class ProductionOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    production_order_id: str
    product: str
    required_component: str
    units_planned: int
    component_required_per_unit: int
    deadline: datetime | date
    priority: str


class SupplierMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: UUID
    supplier_id: str
    direction: str
    subject: str
    body: str
    sent_at: datetime
    responded_at: datetime | None = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: UUID
    type: str
    entity_type: str
    entity_id: str
    severity: str
    message: str
    requires_approval: bool
    status: str
    created_at: datetime


class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    escalation_id: UUID
    alert_id: UUID
    brief: str
    cost_delta: Decimal | None = None
    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class EscalationResolveRequest(BaseModel):
    decision: Literal["approve", "reject"]
    note: str | None = ""


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_id: UUID
    event_type: str
    entity_type: str
    entity_id: str
    actor: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    ts: datetime


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: dict[str, Any] = {}
