from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Integer, BigInteger, Numeric, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id: Mapped[str] = mapped_column(String(32), nullable=False, default="WH-MAIN")
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    erp_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    physical_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    usable_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    damaged_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    blocked_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    in_transit_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="ERP")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    material: Mapped["Material"] = relationship(viewonly=True)  # noqa: F821


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    movement_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    material_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id: Mapped[str] = mapped_column(String(32), nullable=False, default="WH-MAIN")
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(32))
    reference_id: Mapped[str | None] = mapped_column(String(64))
    movement_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_system: Mapped[str] = mapped_column(String(32), nullable=False, default="ERP")
    reason: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        # index added in phase 2 migration where needed
    )
