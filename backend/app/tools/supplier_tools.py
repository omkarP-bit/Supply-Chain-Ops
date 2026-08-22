from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import ContractSupplier


async def query_suppliers_for_component(
    session: AsyncSession, component_id: str
) -> list[dict[str, Any]]:
    """Query suppliers capable of supplying a specific component."""
    result = await session.execute(
        select(ContractSupplier).where(ContractSupplier.component_id == component_id)
    )
    suppliers = result.scalars().all()
    return [
        {
            "supplier_id": s.supplier_id,
            "supplier_name": s.supplier_name,
            "component_id": s.component_id,
            "unit_price": float(s.unit_price),
            "lead_time_days": s.lead_time_days,
            "available_quantity": s.available_quantity,
            "quality_score": float(s.quality_score),
            "reliability_score": float(s.reliability_score),
            "min_order_quantity": s.min_order_quantity,
            "certifications": s.certifications or [],
        }
        for s in suppliers
    ]
