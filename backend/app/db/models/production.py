from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    production_order_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PLANNED")
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    completed_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    production_rate_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=1)
    line_id: Mapped[str | None] = mapped_column(String(32))
    customer_order_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    consumption: Mapped[list["ProductionConsumption"]] = relationship(back_populates="production_order")


class ProductionConsumption(Base):
    __tablename__ = "production_consumption"

    consumption_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    production_order_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("production_orders.production_order_id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    quantity_consumed: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    consumption_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    actual_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="UNIT")

    production_order: Mapped["ProductionOrder"] = relationship(back_populates="consumption")
