from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    po_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    po_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="RESTRICT"), nullable=False
    )
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="RESTRICT"), nullable=False
    )
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_delivery_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONFIRMED")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="NORMAL")
    production_order_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("production_orders.production_order_id", ondelete="SET NULL")
    )
    created_by: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    po_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("purchase_orders.po_id", ondelete="CASCADE"), nullable=False
    )
    tracking_number: Mapped[str | None] = mapped_column(String(64))
    shipment_status: Mapped[str] = mapped_column(String(32), nullable=False, default="LABEL_CREATED")
    label_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatch_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    carrier: Mapped[str | None] = mapped_column(String(64))
    last_tracking_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    tracking_location: Mapped[str | None] = mapped_column(String(128))
    tracking_source: Mapped[str | None] = mapped_column(String(32), default="CARRIER_API")
