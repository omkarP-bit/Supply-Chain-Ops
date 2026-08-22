from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
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
