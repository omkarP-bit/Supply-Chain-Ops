from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import ContractPurchaseOrder


async def get_tracking_status(session: AsyncSession, po_id: str) -> dict[str, Any] | None:
    """Retrieve shipment tracking status and expected delivery for a purchase order."""
    result = await session.execute(
        select(ContractPurchaseOrder).where(ContractPurchaseOrder.po_id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        return None
    return {
        "po_id": po.po_id,
        "supplier_id": po.supplier_id,
        "status": po.status,
        "expected_delivery": po.expected_delivery.isoformat(),
        "is_delayed": po.status == "delayed" or (po.expected_delivery < datetime.now(timezone.utc) and po.status != "delivered"),
    }
