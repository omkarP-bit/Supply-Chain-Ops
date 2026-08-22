from __future__ import annotations

from decimal import Decimal
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.supplier_tools import query_suppliers_for_component
from app.tools.messaging_tools import send_supplier_message


async def broadcast_rfq(
    session: AsyncSession, component_id: str, quantity: int, deadline_days: int
) -> list[dict[str, Any]]:
    """Broadcast Request For Quote (RFQ) to all registered suppliers for a component."""
    suppliers = await query_suppliers_for_component(session, component_id)
    outbound = []
    for s in suppliers:
        msg = await send_supplier_message(
            session,
            supplier_id=s["supplier_id"],
            subject=f"Urgent RFQ: {component_id} ({quantity} units)",
            body=f"Requesting quote for {quantity} units of {component_id} within {deadline_days} days.",
        )
        outbound.append({"supplier_id": s["supplier_id"], "message_id": msg["message_id"]})
    return outbound
