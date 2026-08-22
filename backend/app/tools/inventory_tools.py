from __future__ import annotations

from decimal import Decimal
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import Component
from app.db.models.inventory import InventorySnapshot


async def get_component_inventory(session: AsyncSession, component_id: str) -> dict[str, Any] | None:
    """Retrieve deterministic inventory level, daily usage, and safety stock for a component."""
    result = await session.execute(
        select(Component).where(Component.component_id == component_id)
    )
    comp = result.scalar_one_or_none()
    if not comp:
        return None
    return {
        "component_id": comp.component_id,
        "name": comp.name,
        "current_stock": comp.current_stock,
        "usable_stock": comp.usable_stock,
        "daily_usage": comp.daily_usage,
        "safety_stock": comp.safety_stock,
        "warehouse": comp.warehouse,
        "days_of_coverage": round(comp.usable_stock / comp.daily_usage, 2) if comp.daily_usage > 0 else 999.0,
    }


async def adjust_stock_quantity(
    session: AsyncSession, component_id: str, quantity_delta: int, reason: str
) -> dict[str, Any]:
    """Adjust usable stock deterministically for ERP sync or physical reconciliation."""
    result = await session.execute(
        select(Component).where(Component.component_id == component_id)
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise ValueError(f"Component {component_id} not found")

    old_stock = comp.usable_stock
    comp.usable_stock = max(0, comp.usable_stock + quantity_delta)
    comp.current_stock = max(0, comp.current_stock + quantity_delta)
    await session.flush()

    return {
        "component_id": component_id,
        "old_stock": old_stock,
        "new_stock": comp.usable_stock,
        "delta": quantity_delta,
        "reason": reason,
    }
