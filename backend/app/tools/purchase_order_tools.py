from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.procurement import PurchaseOrder, Shipment


async def create_purchase_order(
    session: AsyncSession,
    supplier_id: str,
    material_id: str,
    quantity: Decimal,
    unit_price: Decimal,
    production_order_id: str | None = None,
) -> dict:
    po_id = str(uuid.uuid4().hex[:16])
    po_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{po_id[:8].upper()}"
    total_cost = quantity * unit_price
    now = datetime.now(timezone.utc)

    po = PurchaseOrder(
        po_id=po_id,
        po_number=po_number,
        supplier_id=supplier_id,
        material_id=material_id,
        ordered_quantity=quantity,
        received_quantity=Decimal("0"),
        remaining_quantity=quantity,
        unit_price=unit_price,
        total_cost=total_cost,
        order_date=now,
        expected_delivery_date=now + timedelta(days=30),
        status="CONFIRMED",
        priority="NORMAL",
        production_order_id=production_order_id,
    )
    session.add(po)

    shipment_id = str(uuid.uuid4().hex[:16])
    shipment = Shipment(
        shipment_id=shipment_id,
        po_id=po_id,
        shipment_status="LABEL_CREATED",
        label_created_at=now,
        tracking_source="CARRIER_API",
    )
    session.add(shipment)

    await session.flush()
    return {"po_id": po_id, "po_number": po_number, "status": po.status}


async def update_purchase_order_status(
    session: AsyncSession, po_id: str, new_status: str
) -> bool:
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_id == po_id)
    )
    po = result.scalar_one_or_none()
    if not po:
        return False
    po.status = new_status
    await session.flush()
    return True


async def split_purchase_order(
    session: AsyncSession, po_id: str, splits: list[dict]
) -> list[dict]:
    result = await session.execute(
        select(PurchaseOrder).where(PurchaseOrder.po_id == po_id)
    )
    original = result.scalar_one_or_none()
    if not original:
        return []

    created: list[dict] = []
    for split in splits:
        qty = Decimal(str(split.get("quantity", 0)))
        new_po_id = str(uuid.uuid4().hex[:16])
        new_po_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{new_po_id[:8].upper()}"

        new_po = PurchaseOrder(
            po_id=new_po_id,
            po_number=new_po_number,
            supplier_id=original.supplier_id,
            material_id=original.material_id,
            ordered_quantity=qty,
            received_quantity=Decimal("0"),
            remaining_quantity=qty,
            unit_price=original.unit_price,
            total_cost=qty * original.unit_price,
            order_date=original.order_date,
            expected_delivery_date=original.expected_delivery_date,
            status="CONFIRMED",
            priority=original.priority,
            production_order_id=split.get("production_order_id", original.production_order_id),
        )
        session.add(new_po)
        created.append({"po_id": new_po_id, "po_number": new_po_number, "quantity": float(qty)})

    await session.flush()
    return created
