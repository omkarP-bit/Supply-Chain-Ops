import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    ARRAY,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Component(Base):
    __tablename__ = "components"

    component_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usable_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safety_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warehouse: Mapped[str | None] = mapped_column(String(128), default="Main WH")
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ContractSupplier(Base):
    __tablename__ = "contract_suppliers"

    supplier_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    component_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("components.component_id", ondelete="SET NULL"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    min_order_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    certifications: Mapped[list[str] | None] = mapped_column(JSONB, default=list)


class ContractPurchaseOrder(Base):
    __tablename__ = "contract_purchase_orders"

    po_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    component_id: Mapped[str] = mapped_column(String(64), ForeignKey("components.component_id", ondelete="CASCADE"), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_delivery: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="in_transit")  # in_transit | delayed | delivered | cancelled
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    approval_required_above: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=150000)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ContractProductionOrder(Base):
    __tablename__ = "contract_production_orders"

    production_order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product: Mapped[str] = mapped_column(String(255), nullable=False)
    required_component: Mapped[str] = mapped_column(String(64), ForeignKey("components.component_id", ondelete="CASCADE"), nullable=False)
    units_planned: Mapped[int] = mapped_column(Integer, nullable=False)
    component_required_per_unit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")  # low | medium | high


class SupplierMessage(Base):
    __tablename__ = "supplier_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False, default="outbound")  # outbound | inbound
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # po_delayed | inventory_below_safety_stock | supplier_response_pending | budget_approval_required | production_schedule_at_risk
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # purchase_order | component | supplier | production_order
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")  # low | medium | high
    message: Mapped[str] = mapped_column(Text, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")  # open | acknowledged | resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Escalation(Base):
    __tablename__ = "escalations"

    escalation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False)
    brief: Mapped[str] = mapped_column(Text, nullable=False)
    cost_delta: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending | approved | rejected
    resolved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # alert_generated | escalation_created | escalation_resolved
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
