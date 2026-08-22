from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class RiskThreshold(Base):
    __tablename__ = "risk_thresholds"

    threshold_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=True
    )
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    warning_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    critical_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="days")
    comparison_operator: Mapped[str] = mapped_column(String(8), nullable=False, default="<")
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="WARNING")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)


class InventoryPricingAdjustment(Base):
    __tablename__ = "inventory_pricing_adjustments"

    adjustment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("suppliers.supplier_id", ondelete="SET NULL"), nullable=True
    )
    batch_id: Mapped[str | None] = mapped_column(String(64))
    original_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    damage_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    quality_degradation: Mapped[str] = mapped_column(String(32), nullable=False, default="NONE")
    adjusted_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    adjustment_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512))
    calculation_method: Mapped[str] = mapped_column(String(64), nullable=False, default="LINEAR_DAMAGE")
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(64))
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
