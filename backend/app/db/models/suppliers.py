from datetime import datetime
from decimal import Decimal

from sqlalchemy import Text, String, Integer, Numeric, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    supplier_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    location: Mapped[str | None] = mapped_column(String(255))
    contact_details: Mapped[dict | None] = mapped_column(JSONB)
    overall_reliability_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    on_time_delivery_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    average_lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    payment_terms: Mapped[str | None] = mapped_column(String(64))
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False, default="LOW")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SupplierMaterial(Base):
    __tablename__ = "supplier_materials"

    supplier_material_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    available_to_promise: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    minimum_order_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=1)
    maximum_order_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    expedited_lead_time_days: Mapped[int | None] = mapped_column(Integer)
    quality_grade: Mapped[str | None] = mapped_column(String(16))
    aql_level: Mapped[str | None] = mapped_column(String(16))
    inspection_standard: Mapped[str | None] = mapped_column(String(64))
    material_grade: Mapped[str | None] = mapped_column(String(64))
    material_specification: Mapped[dict | None] = mapped_column(JSONB)
    measurement_tolerance: Mapped[str | None] = mapped_column(String(64))
    certification_required: Mapped[str | None] = mapped_column(String(128))
    certification_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    certification_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    batch_size: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    production_capacity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SupplierPerformance(Base):
    __tablename__ = "supplier_performance"

    performance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="CASCADE"), nullable=False
    )
    evaluation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orders_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders_on_time: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders_late: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_delay_days: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    quality_rejection_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    eta_change_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claim_mismatch_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tracking_discrepancy_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_response_time: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)


class SupplierCommunication(Base):
    __tablename__ = "supplier_communications"

    communication_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="CASCADE"), nullable=False
    )
    po_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("purchase_orders.po_id", ondelete="SET NULL"))
    message_type: Mapped[str] = mapped_column(String(32), nullable=False, default="STATUS_UPDATE")
    message_text: Mapped[str | None] = mapped_column(Text)
    claimed_status: Mapped[str | None] = mapped_column(String(32))
    claimed_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    claimed_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    claimed_dispatch_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="EMAIL")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupplierQuote(Base):
    __tablename__ = "supplier_quotes"

    quote_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    certification_level: Mapped[str | None] = mapped_column(String(64))
    certification_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    minimum_order_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    quote_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    availability: Mapped[str | None] = mapped_column(String(32))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
