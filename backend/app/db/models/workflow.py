from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False)
    material_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="SET NULL")
    )
    po_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("purchase_orders.po_id", ondelete="SET NULL")
    )
    supplier_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    workflow_state: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    plan_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False
    )
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_details: Mapped[dict | None] = mapped_column(JSONB)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    estimated_delivery_days: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    production_impact_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    supplier_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    robustness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    approval_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("recovery_plans.plan_id", ondelete="SET NULL")
    )
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    approval_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    production_impact: Mapped[str | None] = mapped_column(String(255))
    risk_if_rejected: Mapped[str | None] = mapped_column(String(255))
    alternatives_considered: Mapped[list | None] = mapped_column(JSONB)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    approved_by: Mapped[str | None] = mapped_column(String(64))
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(String(512))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("incidents.incident_id", ondelete="SET NULL")
    )
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    input_data: Mapped[dict | None] = mapped_column(JSONB)
    output_data: Mapped[dict | None] = mapped_column(JSONB)
    reason: Mapped[str | None]
    risk_level: Mapped[str | None] = mapped_column(String(16))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    correlation_id: Mapped[str | None] = mapped_column(String(64))
