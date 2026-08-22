from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import incident_repo, approval_repo, supplier_repo, production_repo
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    open_incidents = await incident_repo.list_incidents(db, status="OPEN", limit=500)
    all_incidents = await incident_repo.list_incidents(db, limit=500)

    critical_count = sum(1 for i in all_incidents if i.severity == "CRITICAL")

    pending_approvals = await approval_repo.list_pending_approvals(db)

    production_at_risk: list[str] = []
    seen_materials: set[str] = set()
    for inc in all_incidents:
        if inc.material_id and inc.material_id not in seen_materials:
            count = await production_repo.count_at_risk(db, inc.material_id)
            if count > 0:
                production_at_risk.append(inc.material_id)
            seen_materials.add(inc.material_id)

    return DashboardResponse(
        active_incidents_count=len(open_incidents),
        critical_risk_count=critical_count,
        pending_approvals_count=len(pending_approvals),
        production_at_risk=production_at_risk,
        recent_incidents=all_incidents[:10],
    )
