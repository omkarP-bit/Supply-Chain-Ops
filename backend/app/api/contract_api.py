import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
from app.schemas.contract_schemas import (
    InventoryOut,
    PurchaseOrderOut,
    PurchaseOrderPatch,
    SupplierOut,
    ProductionOrderOut,
    SupplierMessageOut,
    AlertOut,
    EscalationOut,
    EscalationResolveRequest,
    AuditLogOut,
)
from app.services.alert_rules import scan_all_alerts

router = APIRouter(tags=["contract"])


# --- Task 3: Core Data APIs ---

@router.get("/inventory", response_model=list[InventoryOut])
async def list_inventory(db: AsyncSession = Depends(get_db)):
    stmt = select(Component).order_by(Component.component_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/inventory/{component_id}", response_model=InventoryOut)
async def get_inventory_item(component_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Component).where(Component.component_id == component_id)
    res = await db.execute(stmt)
    comp = res.scalar_one_or_none()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Component {component_id} not found", "detail": {}},
        )
    return comp


@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
async def list_purchase_orders(db: AsyncSession = Depends(get_db)):
    stmt = select(ContractPurchaseOrder).order_by(ContractPurchaseOrder.po_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
async def get_purchase_order(po_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ContractPurchaseOrder).where(ContractPurchaseOrder.po_id == po_id)
    res = await db.execute(stmt)
    po = res.scalar_one_or_none()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Purchase order {po_id} not found", "detail": {}},
        )
    return po


@router.patch("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
async def patch_purchase_order(
    po_id: str,
    payload: PurchaseOrderPatch,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ContractPurchaseOrder).where(ContractPurchaseOrder.po_id == po_id)
    res = await db.execute(stmt)
    po = res.scalar_one_or_none()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Purchase order {po_id} not found", "detail": {}},
        )

    # Optimistic concurrency check
    if po.version != payload.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "conflict",
                "message": f"Version conflict: expected version {po.version}, got {payload.version}",
                "detail": {"current_version": po.version, "provided_version": payload.version},
            },
        )

    before_state = {
        "status": po.status,
        "quantity": po.quantity,
        "unit_price": str(po.unit_price),
        "total_value": str(po.total_value),
        "version": po.version,
    }

    if payload.status is not None:
        po.status = payload.status
    if payload.expected_delivery is not None:
        po.expected_delivery = payload.expected_delivery
    if payload.quantity is not None:
        po.quantity = payload.quantity
        po.total_value = Decimal(str(po.quantity)) * po.unit_price
    if payload.unit_price is not None:
        po.unit_price = payload.unit_price
        po.total_value = Decimal(str(po.quantity)) * po.unit_price

    po.version += 1

    after_state = {
        "status": po.status,
        "quantity": po.quantity,
        "unit_price": str(po.unit_price),
        "total_value": str(po.total_value),
        "version": po.version,
    }

    # Audit log
    db.add(
        AuditLog(
            audit_id=uuid.uuid4(),
            event_type="purchase_order_updated",
            entity_type="purchase_order",
            entity_id=po.po_id,
            actor="user",
            before=before_state,
            after=after_state,
            ts=datetime.now(timezone.utc),
        )
    )

    await db.commit()
    await db.refresh(po)
    return po


@router.get("/contract-suppliers", response_model=list[SupplierOut])
@router.get("/suppliers-list", response_model=list[SupplierOut])
async def list_contract_suppliers(db: AsyncSession = Depends(get_db)):
    stmt = select(ContractSupplier).order_by(ContractSupplier.supplier_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/production-schedule", response_model=list[ProductionOrderOut])
async def get_production_schedule(db: AsyncSession = Depends(get_db)):
    stmt = select(ContractProductionOrder).order_by(ContractProductionOrder.deadline)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/supplier-messages", response_model=list[SupplierMessageOut])
async def get_supplier_messages(db: AsyncSession = Depends(get_db)):
    stmt = select(SupplierMessage).order_by(desc(SupplierMessage.sent_at))
    res = await db.execute(stmt)
    return res.scalars().all()


# --- Task 4: Alert Engine APIs ---

@router.post("/alerts/scan", response_model=list[AlertOut])
async def scan_alerts_endpoint(db: AsyncSession = Depends(get_db)):
    new_alerts = await scan_all_alerts(db)
    return new_alerts


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    status: str | None = Query(None),
    type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert).order_by(desc(Alert.created_at))
    if status:
        stmt = stmt.where(Alert.status == status)
    if type:
        stmt = stmt.where(Alert.type == type)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).where(Alert.alert_id == alert_id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Alert {alert_id} not found", "detail": {}},
        )
    return alert


# --- Task 5: Escalation & Approval APIs ---

@router.get("/escalations", response_model=list[EscalationOut])
async def list_escalations(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Escalation).order_by(desc(Escalation.created_at))
    if status:
        stmt = stmt.where(Escalation.status == status)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/escalations/{escalation_id}/resolve", response_model=EscalationOut)
async def resolve_escalation(
    escalation_id: uuid.UUID,
    payload: EscalationResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Escalation).where(Escalation.escalation_id == escalation_id)
    res = await db.execute(stmt)
    esc = res.scalar_one_or_none()
    if not esc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Escalation {escalation_id} not found", "detail": {}},
        )

    now = datetime.now(timezone.utc)
    before_status = esc.status
    esc.status = "approved" if payload.decision == "approve" else "rejected"
    esc.resolved_by = "procurement_manager"
    esc.resolved_at = now

    # Also resolve linked alert
    alert_stmt = select(Alert).where(Alert.alert_id == esc.alert_id)
    alert_res = await db.execute(alert_stmt)
    linked_alert = alert_res.scalar_one_or_none()
    if linked_alert:
        linked_alert.status = "resolved"

    # Write to audit log
    db.add(
        AuditLog(
            audit_id=uuid.uuid4(),
            event_type="escalation_resolved",
            entity_type=linked_alert.entity_type if linked_alert else "escalation",
            entity_id=linked_alert.entity_id if linked_alert else str(escalation_id),
            actor="procurement_manager",
            before={"status": before_status},
            after={"status": esc.status, "note": payload.note or ""},
            ts=now,
        )
    )

    await db.commit()
    await db.refresh(esc)
    return esc


# --- Task 6: Audit Trail APIs ---

@router.get("/audit-log", response_model=list[AuditLogOut])
async def get_audit_log(
    entity_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).order_by(desc(AuditLog.ts))
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    res = await db.execute(stmt)
    return res.scalars().all()
