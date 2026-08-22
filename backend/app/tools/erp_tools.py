from __future__ import annotations

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.tools.inventory_tools import adjust_stock_quantity
from app.tools.purchase_order_tools import update_purchase_order_status
from app.db.repositories.audit_repo import create_audit_event


async def commit_erp_recovery_actions(
    session: AsyncSession,
    incident_id: str | None,
    action_type: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    """Execute authorized recovery plan changes against simulated ERP system."""
    if action_type == "RESTOCK":
        res = await adjust_stock_quantity(
            session,
            component_id=details["component_id"],
            quantity_delta=details["quantity"],
            reason=f"Recovery action for incident {incident_id}",
        )
    elif action_type == "UPDATE_PO":
        success = await update_purchase_order_status(
            session,
            po_id=details["po_id"],
            new_status=details["status"],
        )
        res = {"po_id": details["po_id"], "updated": success}
    else:
        res = {"action": action_type, "status": "COMMITTED"}

    if incident_id:
        try:
            await create_audit_event(
                session,
                incident_id=incident_id,
                agent_name="ERPUpdateTool",
                event_type="ERP_COMMIT",
                action=action_type,
                input_data=details,
                output_data=res,
            )
        except Exception:
            pass

    return res
