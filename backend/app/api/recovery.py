from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import incident_repo, recovery_repo
from app.engines.risk_engine import OperationalRiskEngine
from app.engines.supplier_engine import SupplierEvaluationEngine
from app.schemas.recovery import AnalysisResponse, PlanResponse
from app.services.llm_provider import get_plan_suggestions
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/v1", tags=["recovery"])

risk_engine = OperationalRiskEngine()
supplier_engine = SupplierEvaluationEngine()
workflow_service = WorkflowService()


@router.post("/incidents/{incident_id}/analyze", response_model=AnalysisResponse)
async def analyze_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
):
    incident = await incident_repo.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not incident.material_id:
        raise HTTPException(status_code=400, detail="Incident has no associated material")

    risk_report = await risk_engine.calculate_risk(db, incident.material_id)

    candidates = await supplier_engine.get_supplier_candidates(
        db, incident.material_id, Decimal("100"), None
    )

    risk_dict = {
        "material_id": str(risk_report.material_id),
        "risk_level": risk_report.risk_level,
        "usable_stock": float(risk_report.usable_stock),
        "coverage_days": float(risk_report.coverage_days),
        "discrepancy_percentage": float(risk_report.discrepancy_percentage),
        "hours_to_production_stop": risk_report.hours_to_production_stop,
        "trend_7d_vs_30d": risk_report.trend_7d_vs_30d,
        "threshold_violations": risk_report.threshold_violations,
    }

    suppliers_list = [
        {
            "supplier_id": str(c.supplier_id),
            "supplier_name": c.supplier_name,
            "available_quantity": float(c.available_quantity),
            "unit_price": float(c.unit_price),
            "lead_time_days": c.lead_time_days,
            "certification_valid": c.certification_valid,
            "quality_score": float(c.quality_score),
            "reliability_score": float(c.reliability_score),
            "score": float(c.score),
            "rejection_reason": c.rejection_reason,
        }
        for c in candidates
    ]

    return AnalysisResponse(
        incident_id=incident_id,
        risk_report=risk_dict,
        eligible_suppliers=suppliers_list,
    )


@router.post("/incidents/{incident_id}/recommend", response_model=list[PlanResponse])
async def recommend_plans(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
):
    incident = await incident_repo.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not incident.material_id:
        raise HTTPException(status_code=400, detail="Incident has no associated material")

    risk_report = await risk_engine.calculate_risk(db, incident.material_id)

    candidates = await supplier_engine.get_supplier_candidates(db, incident.material_id, Decimal("100"), None)

    risk_dict = {
        "material_id": str(risk_report.material_id),
        "risk_level": risk_report.risk_level,
        "usable_stock": float(risk_report.usable_stock),
        "coverage_days": float(risk_report.coverage_days),
        "discrepancy_percentage": float(risk_report.discrepancy_percentage),
        "hours_to_production_stop": risk_report.hours_to_production_stop,
        "trend_7d_vs_30d": risk_report.trend_7d_vs_30d,
        "threshold_violations": risk_report.threshold_violations,
    }

    suppliers_list = [
        {
            "supplier_id": str(c.supplier_id),
            "supplier_name": c.supplier_name,
            "available_quantity": float(c.available_quantity),
            "unit_price": float(c.unit_price),
            "lead_time_days": c.lead_time_days,
            "certification_valid": c.certification_valid,
            "quality_score": float(c.quality_score),
            "reliability_score": float(c.reliability_score),
            "score": float(c.score),
            "rejection_reason": c.rejection_reason,
        }
        for c in candidates
    ]

    suggestions = await get_plan_suggestions(
        incident_id=incident_id,
        material_id=incident.material_id,
        risk_report=risk_dict,
        eligible_suppliers=suppliers_list,
    )

    created_plans: list[PlanResponse] = []
    for s in suggestions:
        plan = await recovery_repo.create_plan(
            db,
            plan_id=s["plan_id"],
            incident_id=incident_id,
            plan_name=s["plan_name"],
            plan_type=s["plan_type"],
            plan_details={**(s.get("plan_details") or {}), "material_id": incident.material_id},
            estimated_cost=Decimal(str(s.get("estimated_cost", 0))),
            estimated_delivery_days=Decimal(str(s.get("estimated_delivery_days", 0))),
            production_impact_hours=Decimal(str(s.get("production_impact_hours", 0))),
            supplier_risk_score=Decimal(str(s.get("supplier_risk_score", 0))),
            quality_score=Decimal(str(s.get("quality_score", 0))),
            robustness_score=Decimal(str(s.get("robustness_score", 0))),
            overall_score=Decimal(str(s.get("overall_score", 0))),
        )
        created_plans.append(plan)

    valid_plans = [p for p in created_plans if p.status != "INVALID"]
    if valid_plans:
        await workflow_service.request_plan_approval(db, valid_plans[0].plan_id)

    return created_plans


@router.get("/incidents/{incident_id}/plans", response_model=list[PlanResponse])
async def list_plans(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
):
    incident = await incident_repo.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await recovery_repo.list_plans_for_incident(db, incident_id)
