from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import ContractProductionOrder


async def get_production_schedule(session: AsyncSession) -> list[dict[str, Any]]:
    """Fetch all scheduled production orders and required component quantities."""
    result = await session.execute(
        select(ContractProductionOrder).order_by(ContractProductionOrder.deadline.asc())
    )
    orders = result.scalars().all()
    return [
        {
            "production_order_id": po.production_order_id,
            "product": po.product,
            "required_component": po.required_component,
            "units_planned": po.units_planned,
            "component_required_per_unit": po.component_required_per_unit,
            "total_components_needed": po.units_planned * po.component_required_per_unit,
            "deadline": po.deadline.isoformat(),
            "priority": po.priority,
        }
        for po in orders
    ]


async def reschedule_production_order(
    session: AsyncSession, production_order_id: str, new_deadline: datetime
) -> dict[str, Any]:
    """Reschedule a production order deadline when recovery timeline dictates."""
    result = await session.execute(
        select(ContractProductionOrder).where(
            ContractProductionOrder.production_order_id == production_order_id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise ValueError(f"Production order {production_order_id} not found")

    old_deadline = order.deadline
    order.deadline = new_deadline
    await session.flush()

    return {
        "production_order_id": production_order_id,
        "old_deadline": old_deadline.isoformat(),
        "new_deadline": order.deadline.isoformat(),
    }


async def prioritize_production_orders(
    session: AsyncSession, component_id: str, available_stock: float
) -> dict[str, Any]:
    """Deterministically prioritize production orders based on deadline, priority level, and stock allocation."""
    result = await session.execute(
        select(ContractProductionOrder)
        .where(ContractProductionOrder.required_component == component_id)
        .order_by(
            ContractProductionOrder.priority.desc(),
            ContractProductionOrder.deadline.asc(),
        )
    )
    orders = result.scalars().all()

    remaining_stock = Decimal(str(available_stock))
    fulfilled: list[dict[str, Any]] = []
    delayed: list[dict[str, Any]] = []

    for o in orders:
        needed = Decimal(str(o.units_planned * o.component_required_per_unit))
        if remaining_stock >= needed:
            remaining_stock -= needed
            fulfilled.append({
                "production_order_id": o.production_order_id,
                "product": o.product,
                "units_planned": o.units_planned,
                "status": "PROTECTED",
                "priority": o.priority,
                "deadline": o.deadline.isoformat(),
            })
        else:
            delayed.append({
                "production_order_id": o.production_order_id,
                "product": o.product,
                "units_planned": o.units_planned,
                "shortage": float(needed - remaining_stock),
                "status": "DELAYED_OR_RESCHEDULED",
                "priority": o.priority,
                "deadline": o.deadline.isoformat(),
            })

    return {
        "component_id": component_id,
        "total_available_stock": available_stock,
        "remaining_unallocated_stock": float(remaining_stock),
        "fulfilled_orders": fulfilled,
        "delayed_orders": delayed,
    }
