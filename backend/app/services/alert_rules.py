import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import (
    Component,
    ContractPurchaseOrder,
    ContractProductionOrder,
    SupplierMessage,
    Alert,
    Escalation,
    AuditLog,
)


async def check_po_delayed(session: AsyncSession) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    stmt = select(ContractPurchaseOrder).where(
        and_(
            ContractPurchaseOrder.status.notin_(["delivered", "cancelled"]),
        )
    )
    res = await session.execute(stmt)
    pos = res.scalars().all()

    alerts_to_create = []
    for po in pos:
        is_past = po.expected_delivery and po.expected_delivery.astimezone(timezone.utc) < now
        is_delayed_status = po.status == "delayed"
        if is_past or is_delayed_status:
            delivery_str = po.expected_delivery.strftime("%Y-%m-%d") if po.expected_delivery else "N/A"
            alerts_to_create.append({
                "type": "po_delayed",
                "entity_type": "purchase_order",
                "entity_id": po.po_id,
                "severity": "high" if is_delayed_status else "medium",
                "message": f"Purchase order {po.po_id} for component {po.component_id} is delayed. Expected delivery was {delivery_str}.",
                "requires_approval": False,
            })
    return alerts_to_create


async def check_inventory_below_safety_stock(session: AsyncSession) -> list[dict[str, Any]]:
    stmt = select(Component).where(Component.usable_stock < Component.safety_stock)
    res = await session.execute(stmt)
    components = res.scalars().all()

    alerts_to_create = []
    for comp in components:
        severity = "high" if comp.usable_stock <= (comp.safety_stock * 0.5) else "medium"
        alerts_to_create.append({
            "type": "inventory_below_safety_stock",
            "entity_type": "component",
            "entity_id": comp.component_id,
            "severity": severity,
            "message": f"Component {comp.component_id} ({comp.name}) usable stock {comp.usable_stock} is below safety stock {comp.safety_stock}.",
            "requires_approval": False,
        })
    return alerts_to_create


async def check_supplier_response_pending(session: AsyncSession, threshold_hours: int = 48) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=threshold_hours)

    stmt = select(SupplierMessage).where(
        and_(
            SupplierMessage.direction == "outbound",
            SupplierMessage.responded_at.is_(None),
            SupplierMessage.sent_at <= cutoff,
        )
    )
    res = await session.execute(stmt)
    messages = res.scalars().all()

    alerts_to_create = []
    for msg in messages:
        sent_str = msg.sent_at.strftime("%Y-%m-%d %H:%M") if msg.sent_at else "N/A"
        alerts_to_create.append({
            "type": "supplier_response_pending",
            "entity_type": "supplier",
            "entity_id": msg.supplier_id,
            "severity": "medium",
            "message": f"Supplier {msg.supplier_id} has not responded to inquiry '{msg.subject}' sent at {sent_str} (>{threshold_hours}h ago).",
            "requires_approval": False,
        })
    return alerts_to_create


async def check_budget_approval_required(session: AsyncSession) -> list[dict[str, Any]]:
    stmt = select(ContractPurchaseOrder).where(
        ContractPurchaseOrder.total_value > ContractPurchaseOrder.approval_required_above
    )
    res = await session.execute(stmt)
    pos = res.scalars().all()

    alerts_to_create = []
    for po in pos:
        delta = po.total_value - po.approval_required_above
        alerts_to_create.append({
            "type": "budget_approval_required",
            "entity_type": "purchase_order",
            "entity_id": po.po_id,
            "severity": "high",
            "message": f"Estimated cost {po.total_value} exceeds approval threshold {po.approval_required_above}",
            "requires_approval": True,
            "cost_delta": delta,
            "brief": f"PO-{po.po_id} replacement cost exceeds threshold by {delta}",
        })
    return alerts_to_create


async def check_production_schedule_at_risk(session: AsyncSession, horizon_days: int = 14) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    horizon_dt = now + timedelta(days=horizon_days)

    stmt = select(ContractProductionOrder, Component).join(
        Component, ContractProductionOrder.required_component == Component.component_id
    ).where(ContractProductionOrder.deadline <= horizon_dt)

    res = await session.execute(stmt)
    rows = res.all()

    alerts_to_create = []
    for prod_order, comp in rows:
        deadline_dt = prod_order.deadline.astimezone(timezone.utc) if prod_order.deadline.tzinfo else prod_order.deadline.replace(tzinfo=timezone.utc)
        days_left = max((deadline_dt - now).total_seconds() / 86400.0, 0.1)

        daily_usage = comp.daily_usage if comp.daily_usage > 0 else 1
        coverage_days = comp.usable_stock / daily_usage

        if coverage_days < days_left:
            alerts_to_create.append({
                "type": "production_schedule_at_risk",
                "entity_type": "production_order",
                "entity_id": prod_order.production_order_id,
                "severity": "high" if prod_order.priority == "high" else "medium",
                "message": f"Production order {prod_order.production_order_id} deadline ({deadline_dt.strftime('%Y-%m-%d')}) is at risk. Component {comp.component_id} coverage ({coverage_days:.1f} days) is less than {days_left:.1f} days remaining.",
                "requires_approval": False,
            })
    return alerts_to_create


async def scan_all_alerts(session: AsyncSession) -> list[Alert]:
    # 1. Run all 5 rules
    candidates = []
    candidates.extend(await check_po_delayed(session))
    candidates.extend(await check_inventory_below_safety_stock(session))
    candidates.extend(await check_supplier_response_pending(session))
    candidates.extend(await check_budget_approval_required(session))
    candidates.extend(await check_production_schedule_at_risk(session))

    # 2. Query open alerts to avoid duplication for same entity + type
    open_stmt = select(Alert).where(Alert.status == "open")
    open_res = await session.execute(open_stmt)
    existing_open = {(a.type, a.entity_id): a for a in open_res.scalars().all()}

    newly_created_alerts: list[Alert] = []

    for c in candidates:
        key = (c["type"], c["entity_id"])
        if key in existing_open:
            continue

        alert_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        alert = Alert(
            alert_id=alert_id,
            type=c["type"],
            entity_type=c["entity_type"],
            entity_id=c["entity_id"],
            severity=c.get("severity", "medium"),
            message=c["message"],
            requires_approval=c.get("requires_approval", False),
            status="open",
            created_at=now,
        )
        session.add(alert)
        existing_open[key] = alert
        newly_created_alerts.append(alert)

        # Audit log for alert generation
        session.add(
            AuditLog(
                audit_id=uuid.uuid4(),
                event_type="alert_generated",
                entity_type=c["entity_type"],
                entity_id=c["entity_id"],
                actor=None,
                before=None,
                after={
                    "alert_id": str(alert_id),
                    "type": c["type"],
                    "severity": c.get("severity", "medium"),
                    "message": c["message"],
                },
                ts=now,
            )
        )

        # Auto-escalation if requires_approval is True
        if c.get("requires_approval", False):
            esc_id = uuid.uuid4()
            escalation = Escalation(
                escalation_id=esc_id,
                alert_id=alert_id,
                brief=c.get("brief", c["message"]),
                cost_delta=Decimal(str(c.get("cost_delta", 0))) if c.get("cost_delta") is not None else None,
                status="pending",
                created_at=now,
            )
            session.add(escalation)

            session.add(
                AuditLog(
                    audit_id=uuid.uuid4(),
                    event_type="escalation_created",
                    entity_type=c["entity_type"],
                    entity_id=c["entity_id"],
                    actor=None,
                    before=None,
                    after={
                        "escalation_id": str(esc_id),
                        "alert_id": str(alert_id),
                        "status": "pending",
                        "brief": escalation.brief,
                    },
                    ts=now,
                )
            )

    await session.commit()
    return newly_created_alerts
