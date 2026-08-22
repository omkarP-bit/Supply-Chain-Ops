import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import (
    Component,
    ContractSupplier,
    ContractPurchaseOrder,
    ContractProductionOrder,
    SupplierMessage,
    Alert,
    Escalation,
    AuditLog,
)


def _load_fixture(filename: str) -> list[dict]:
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, "fixtures", filename)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    return datetime.fromisoformat(val.replace("Z", "+00:00"))


async def seed_contract_data(session: AsyncSession) -> None:
    comp_count = await session.execute(select(func.count()).select_from(Component))
    if comp_count.scalar() > 0:
        return

    # 1. Components
    components_data = _load_fixture("components.json")
    for c in components_data:
        session.add(
            Component(
                component_id=c["component_id"],
                name=c["name"],
                current_stock=c["current_stock"],
                usable_stock=c["usable_stock"],
                daily_usage=c["daily_usage"],
                safety_stock=c["safety_stock"],
                warehouse=c.get("warehouse", "Main WH"),
            )
        )
    await session.flush()

    # 2. Suppliers
    suppliers_data = _load_fixture("suppliers.json")
    for s in suppliers_data:
        session.add(
            ContractSupplier(
                supplier_id=s["supplier_id"],
                supplier_name=s["supplier_name"],
                component_id=s.get("component_id"),
                unit_price=Decimal(str(s["unit_price"])),
                lead_time_days=s["lead_time_days"],
                available_quantity=s["available_quantity"],
                quality_score=Decimal(str(s["quality_score"])),
                reliability_score=Decimal(str(s["reliability_score"])),
                min_order_quantity=s.get("min_order_quantity", 1),
                certifications=s.get("certifications", []),
            )
        )
    await session.flush()

    # 3. Purchase Orders
    pos_data = _load_fixture("purchase_orders.json")
    for p in pos_data:
        session.add(
            ContractPurchaseOrder(
                po_id=p["po_id"],
                component_id=p["component_id"],
                supplier_id=p["supplier_id"],
                quantity=p["quantity"],
                expected_delivery=_parse_dt(p["expected_delivery"]),
                status=p.get("status", "in_transit"),
                unit_price=Decimal(str(p["unit_price"])),
                total_value=Decimal(str(p["total_value"])),
                approval_required_above=Decimal(str(p.get("approval_required_above", 150000))),
                version=p.get("version", 1),
            )
        )
    await session.flush()

    # 4. Production Orders
    prod_data = _load_fixture("production_orders.json")
    for pr in prod_data:
        session.add(
            ContractProductionOrder(
                production_order_id=pr["production_order_id"],
                product=pr["product"],
                required_component=pr["required_component"],
                units_planned=pr["units_planned"],
                component_required_per_unit=pr.get("component_required_per_unit", 1),
                deadline=_parse_dt(pr["deadline"]),
                priority=pr.get("priority", "medium"),
            )
        )
    await session.flush()

    # 5. Supplier Messages
    msg_data = _load_fixture("supplier_messages.json")
    for m in msg_data:
        session.add(
            SupplierMessage(
                message_id=uuid.UUID(m["message_id"]),
                supplier_id=m["supplier_id"],
                direction=m.get("direction", "outbound"),
                subject=m["subject"],
                body=m["body"],
                sent_at=_parse_dt(m["sent_at"]),
                responded_at=_parse_dt(m.get("responded_at")),
            )
        )

    await session.commit()
