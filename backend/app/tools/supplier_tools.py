from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.contract_models import ContractSupplier
from app.db.models.suppliers import Supplier, SupplierPerformance, SupplierCommunication
from app.db.repositories.audit_repo import create_audit_event


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


async def record_supplier_performance(
    session: AsyncSession,
    supplier_id: str,
    *,
    on_time: bool = True,
    delay_days: float = 0.0,
    quality_passed: bool = True,
    claim_mismatch: bool = False,
) -> dict[str, Any]:
    """Persist structured historical performance metrics in PostgreSQL."""
    stmt = (
        select(SupplierPerformance)
        .where(SupplierPerformance.supplier_id == supplier_id)
        .order_by(SupplierPerformance.evaluation_date.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    perf = res.scalar_one_or_none()

    if not perf:
        perf = SupplierPerformance(
            supplier_id=supplier_id,
            evaluation_date=datetime.now(timezone.utc),
            orders_completed=1,
            orders_on_time=1 if on_time else 0,
            orders_late=0 if on_time else 1,
            average_delay_days=Decimal(str(delay_days)),
            quality_rejection_rate=Decimal("0.0") if quality_passed else Decimal("1.0"),
            claim_mismatch_count=1 if claim_mismatch else 0,
            reliability_score=Decimal("95.0") if on_time and not claim_mismatch else Decimal("60.0"),
            quality_score=Decimal("95.0") if quality_passed else Decimal("50.0"),
        )
        session.add(perf)
    else:
        perf.orders_completed += 1
        if on_time:
            perf.orders_on_time += 1
        else:
            perf.orders_late += 1
        if claim_mismatch:
            perf.claim_mismatch_count += 1
        if not quality_passed:
            perf.quality_rejection_rate = Decimal("0.2")

    await session.flush()
    return {
        "supplier_id": supplier_id,
        "orders_completed": perf.orders_completed,
        "orders_on_time": perf.orders_on_time,
        "claim_mismatches": perf.claim_mismatch_count,
        "reliability_score": float(perf.reliability_score),
    }


async def verify_supplier_claim(
    session: AsyncSession,
    supplier_id: str,
    po_id: str,
    claimed_status: str,
    actual_tracking_status: str,
) -> dict[str, Any]:
    """Verify supplier claim against actual operational/carrier tracking state."""
    discrepancy = False
    details = "Claim matches carrier tracking"

    if claimed_status.upper() in ("DISPATCHED", "IN_TRANSIT", "DELIVERED"):
        if actual_tracking_status.upper() in ("LABEL_CREATED", "PENDING_PICKUP", "NOT_FOUND"):
            discrepancy = True
            details = f"Misleading claim: Supplier claims '{claimed_status}' but carrier tracking indicates '{actual_tracking_status}'."

    now = datetime.now(timezone.utc)
    comm = SupplierCommunication(
        supplier_id=supplier_id,
        po_id=po_id,
        message_type="CLAIM_VERIFICATION",
        claimed_status=claimed_status,
        message_text=details,
        received_at=now,
        channel="SYSTEM_CHECK",
    )
    session.add(comm)
    await session.flush()

    if discrepancy:
        await record_supplier_performance(session, supplier_id, on_time=False, claim_mismatch=True)
        await create_audit_event(
            session,
            incident_id=None,
            agent_name="SupplierClaimVerifier",
            event_type="CLAIM_MISMATCH_DETECTED",
            action="verify_supplier_claim",
            input_data={"supplier_id": supplier_id, "po_id": po_id, "claim": claimed_status},
            output_data={"discrepancy": True, "details": details},
            risk_level="HIGH",
        )

    return {
        "supplier_id": supplier_id,
        "po_id": po_id,
        "discrepancy_detected": discrepancy,
        "details": details,
    }
