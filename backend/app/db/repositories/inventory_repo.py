from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.inventory import InventorySnapshot, InventoryMovement

async def get_latest_snapshot(session: AsyncSession, material_id: str) -> InventorySnapshot | None:
    q = select(InventorySnapshot).where(InventorySnapshot.material_id == material_id).order_by(InventorySnapshot.snapshot_date.desc()).limit(1)
    return (await session.execute(q)).scalar_one_or_none()

async def get_snapshot_history(session: AsyncSession, material_id: str, days: int = 35) -> list[InventorySnapshot]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(InventorySnapshot).where(InventorySnapshot.material_id == material_id, InventorySnapshot.snapshot_date >= cutoff).order_by(InventorySnapshot.snapshot_date.asc())
    return list((await session.execute(q)).scalars())

async def get_consumption_total(session: AsyncSession, material_id: str, days: int) -> Decimal:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(InventoryMovement.material_id == material_id, InventoryMovement.movement_type == "CONSUMPTION", InventoryMovement.movement_timestamp >= cutoff)
    return (await session.execute(q)).scalar()

async def get_movements(session: AsyncSession, material_id: str, days: int = 35) -> list[InventoryMovement]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    q = select(InventoryMovement).where(InventoryMovement.material_id == material_id, InventoryMovement.movement_timestamp >= cutoff).order_by(InventoryMovement.movement_timestamp.asc())
    return list((await session.execute(q)).scalars())
