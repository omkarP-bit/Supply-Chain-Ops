from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.contract_models import Component
from app.db.models.materials import Material
from app.db.repositories import incident_repo, approval_repo, supplier_repo, production_repo, recovery_repo, inventory_repo
from app.engines.risk_engine import OperationalRiskEngine
from app.schemas.dashboard import (
    DashboardResponse,
    CriticalIncidentItem,
    ProductionRiskItem,
    PendingApprovalItem,
)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])
risk_engine = OperationalRiskEngine()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    all_incidents = await incident_repo.list_incidents(db, limit=500)
    open_incidents = [i for i in all_incidents if i.status not in ("RESOLVED", "COMPLETED")]
    critical_count = sum(1 for i in all_incidents if i.severity in ("CRITICAL", "HIGH"))

    pending_approvals_raw = await approval_repo.list_pending_approvals(db)

    # 1. Critical Incidents List (Strict 1-per-component deduplication)
    seen_materials = set()
    critical_incidents: list[CriticalIncidentItem] = []
    for inc in all_incidents:
        mat = inc.material_id or "UNKNOWN"
        if mat in seen_materials:
            continue
        seen_materials.add(mat)

        cov_days = 0.0
        prod_impact = 0.0
        appr_status = "NOT_REQUIRED"

        if inc.material_id:
            try:
                cov = await risk_engine.calculate_inventory_coverage(db, inc.material_id)
                cov_days = float(cov.get("coverage_days", 0.0))
                hours = await risk_engine.calculate_hours_to_production_stop(db, inc.material_id)
                prod_impact = float(hours) if hours < float("inf") else 0.0
            except Exception:
                pass

        # Check approval status
        plans = await recovery_repo.list_plans_for_incident(db, inc.incident_id)
        if plans:
            for p in plans:
                appr = await approval_repo.get_pending_approval_for_plan(db, p.plan_id)
                if appr:
                    appr_status = appr.status
                    break

        # Look up material/component name
        mat_name = None
        if inc.material_id:
            comp_obj = await db.get(Component, inc.material_id)
            if comp_obj:
                mat_name = comp_obj.name
            else:
                mat_obj = await db.get(Material, inc.material_id)
                mat_name = mat_obj.name if mat_obj else inc.material_id

        critical_incidents.append(
            CriticalIncidentItem(
                incident_id=inc.incident_id,
                po_id=inc.po_id,
                material_id=inc.material_id or "UNKNOWN",
                material_name=mat_name,
                incident_type=inc.incident_type or "DISRUPTION",
                severity=inc.severity or "MEDIUM",
                production_impact_hours=prod_impact,
                coverage_days=cov_days,
                status=inc.status or "DETECTED",
                approval_status=appr_status,
                created_at=inc.created_at,
            )
        )
        if len(critical_incidents) >= 15:
            break

    # 2. Production at Risk (Sorted by urgency: Critical -> High -> Medium, then lowest coverage)
    production_at_risk: list[ProductionRiskItem] = []
    comp_res = await db.execute(select(Component))
    components = comp_res.scalars().all()

    components_at_risk_count = 0
    for comp in components:
        usable = float(comp.usable_stock or 0)
        safety = float(comp.safety_stock or 0)
        daily = float(comp.daily_usage or 1)
        cov = usable / daily if daily > 0 else 999.0
        hours = cov * 24.0

        risk_level = "LOW"
        if usable <= safety * 0.5 or cov < 3.0:
            risk_level = "CRITICAL"
            components_at_risk_count += 1
        elif usable <= safety or cov < 7.0:
            risk_level = "HIGH"
            components_at_risk_count += 1
        elif usable <= safety * 1.5 or cov < 14.0:
            risk_level = "MEDIUM"

        if risk_level in ("CRITICAL", "HIGH", "MEDIUM"):
            production_at_risk.append(
                ProductionRiskItem(
                    material_id=comp.component_id,
                    material_name=comp.name,
                    usable_stock=usable,
                    safety_stock=safety,
                    coverage_days=round(cov, 1),
                    hours_to_stop=round(hours, 1),
                    affected_orders_count=1 if risk_level in ("CRITICAL", "HIGH") else 0,
                    risk_level=risk_level,
                )
            )

    # Sort production risks by urgency: CRITICAL first, then lowest coverage days
    risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    production_at_risk.sort(key=lambda x: (risk_order.get(x.risk_level, 9), x.coverage_days, x.hours_to_stop))

    # 3. Pending Approvals Requiring Action (Unique per incident)
    seen_appr_incidents = set()
    pending_approvals: list[PendingApprovalItem] = []
    for appr in pending_approvals_raw:
        if appr.incident_id in seen_appr_incidents:
            continue
        seen_appr_incidents.add(appr.incident_id)

        supplier_name = "Approved Alternate Supplier"
        mat_id = "COMP-104"
        lead_time = 2
        prod_impact = 0.0
        reason = appr.production_impact or "Emergency restock required to prevent production stoppage"

        if appr.plan_id:
            plan = await recovery_repo.get_plan(db, appr.plan_id)
            if plan:
                details = plan.plan_details or {}
                supplier_name = details.get("supplier_name", details.get("supplier_id", "Alternate Supplier"))
                mat_id = details.get("material_id", mat_id)
                lead_time = int(plan.estimated_delivery_days or details.get("lead_time_days", 2))
                prod_impact = float(plan.production_impact_hours or 0.0)
                reason = details.get("rationale", details.get("action", reason))

        pending_approvals.append(
            PendingApprovalItem(
                approval_id=appr.approval_id,
                incident_id=appr.incident_id,
                plan_id=appr.plan_id,
                supplier_name=supplier_name,
                material_id=mat_id,
                requested_amount=float(appr.requested_amount or 0.0),
                lead_time_days=lead_time,
                production_impact_hours=prod_impact,
                risk_level="HIGH" if float(appr.requested_amount or 0) > 75000 else "MEDIUM",
                recommendation_reason=reason,
                status=appr.status,
                created_at=getattr(appr, "created_at", getattr(appr, "requested_at", None)),
            )
        )

    # 4. Status Summary (Reflects unique operational items)
    status_counts: dict[str, int] = {
        "ACTIVE": len(critical_incidents),
        "AWAITING_APPROVAL": len(pending_approvals),
        "EXECUTING": sum(1 for i in critical_incidents if i.status == "EXECUTING"),
        "RESOLVED": sum(1 for i in critical_incidents if i.status in ("RESOLVED", "COMPLETED")),
    }

    return DashboardResponse(
        active_incidents_count=len(critical_incidents),
        critical_risk_count=sum(1 for i in critical_incidents if i.severity in ("CRITICAL", "HIGH")),
        pending_approvals_count=len(pending_approvals),
        components_at_risk_count=components_at_risk_count,
        critical_incidents=critical_incidents,
        production_at_risk=production_at_risk,
        pending_approvals=pending_approvals,
        status_summary=status_counts,
        recent_incidents=critical_incidents[:5],
    )
