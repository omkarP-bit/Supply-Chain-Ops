from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import incident_repo, recovery_repo, audit_repo
from app.engines.validation_engine import PlanValidationEngine
from app.engines.simulation_engine import SimulationEngine
from app.services.llm_provider import get_plan_suggestions


class RecoveryRecommendationAgent:

    def __init__(self):
        self.validation_engine = PlanValidationEngine()
        self.simulation_engine = SimulationEngine()

    async def generate_plans(self, session: AsyncSession, incident_id: str) -> list[dict]:
        incident = await incident_repo.get_incident(session, incident_id)
        if not incident:
            return []

        state = incident.workflow_state or {}
        analysis = state.get("analysis", {})
        risk_report = analysis.get("risk_report") or {}
        eligible_suppliers = analysis.get("eligible_suppliers") or []

        raw_suggestions = await get_plan_suggestions(
            incident_id=incident_id,
            material_id=incident.material_id,
            risk_report=risk_report,
            eligible_suppliers=eligible_suppliers,
        )

        saved_plans: list[dict] = []
        for suggestion in raw_suggestions:
            plan_dict = self._suggestion_to_plan_dict(incident_id, suggestion)
            plan_dict["material_id"] = incident.material_id
            plan_dict["plan_details"] = {
                **(plan_dict.get("plan_details") or {}),
                "material_id": incident.material_id,
            }

            validation_report = await self.validation_engine.validate_plan(session, plan_dict)

            sim_result = await self.simulation_engine.simulate_plan(session, plan_dict)

            plan_dict["overall_score"] = round(
                suggestion.get("overall_score", 0)
                * (1.0 if validation_report.valid else 0.5),
                2,
            )
            plan_dict["status"] = "PROPOSED" if validation_report.valid else "INVALID"

            await audit_repo.create_audit_event(
                session,
                incident_id=incident_id,
                agent_name="RecoveryRecommendationAgent",
                event_type="PLAN_VALIDATION",
                action="plan_validated",
                input_data={"plan_id": plan_dict["plan_id"]},
                output_data={
                    "valid": validation_report.valid,
                    "violations": validation_report.violations,
                    "simulation_feasible": sim_result.feasible,
                },
            )

            plan = await recovery_repo.create_plan(
                session,
                incident_id=incident_id,
                plan_id=plan_dict["plan_id"],
                plan_name=plan_dict["plan_name"],
                plan_type=plan_dict["plan_type"],
                plan_details=plan_dict.get("plan_details"),
                estimated_cost=Decimal(str(plan_dict.get("estimated_cost", 0))),
                estimated_delivery_days=Decimal(str(plan_dict.get("estimated_delivery_days", 0))),
                production_impact_hours=Decimal(str(plan_dict.get("production_impact_hours", 0))),
                supplier_risk_score=Decimal(str(plan_dict.get("supplier_risk_score", 0))),
                quality_score=Decimal(str(plan_dict.get("quality_score", 0))),
                robustness_score=Decimal(str(plan_dict.get("robustness_score", 0))),
                overall_score=Decimal(str(plan_dict["overall_score"])),
                status=plan_dict["status"],
            )

            saved_plans.append({
                "plan_id": plan.plan_id,
                "plan_name": plan.plan_name,
                "plan_type": plan.plan_type,
                "plan_details": plan.plan_details,
                "estimated_cost": float(plan.estimated_cost),
                "estimated_delivery_days": float(plan.estimated_delivery_days),
                "production_impact_hours": float(plan.production_impact_hours),
                "supplier_risk_score": float(plan.supplier_risk_score),
                "quality_score": float(plan.quality_score),
                "robustness_score": float(plan.robustness_score),
                "overall_score": float(plan.overall_score),
                "status": plan.status,
            })

        await audit_repo.create_audit_event(
            session,
            incident_id=incident_id,
            agent_name="RecoveryRecommendationAgent",
            event_type="RECOMMENDATION",
            action="plans_generated",
            input_data={"plan_count": len(saved_plans)},
            output_data={"plan_ids": [p["plan_id"] for p in saved_plans]},
        )

        return saved_plans

    async def recommend(self, session: AsyncSession, incident_id: str) -> dict:
        plans = await self.generate_plans(session, incident_id)
        if not plans:
            return {"incident_id": incident_id, "recommended_plan": None, "plans": []}

        best = max(plans, key=lambda p: p["overall_score"])

        await recovery_repo.update_plan_status(session, best["plan_id"], "SELECTED")
        best["status"] = "SELECTED"

        return {
            "incident_id": incident_id,
            "recommended_plan": best["plan_id"],
            "plans": plans,
        }

    def _suggestion_to_plan_dict(self, incident_id: str, suggestion: dict) -> dict:
        details = suggestion.get("plan_details", {})
        return {
            "plan_id": suggestion.get("plan_id", str(uuid.uuid4().hex[:16])),
            "plan_name": suggestion.get("plan_name", "Unnamed plan"),
            "plan_type": suggestion.get("plan_type", "UNKNOWN"),
            "plan_details": details,
            "material_id": details.get("material_id"),
            "supplier_id": details.get("supplier_id"),
            "required_quantity": details.get("quantity", 0),
            "unit_price": details.get("unit_price", 0),
            "total_cost": suggestion.get("estimated_cost", 0),
            "deadline_days": details.get("lead_time_days"),
            "estimated_cost": suggestion.get("estimated_cost", 0),
            "estimated_delivery_days": suggestion.get("estimated_delivery_days", 0),
            "production_impact_hours": suggestion.get("production_impact_hours", 0),
            "supplier_risk_score": suggestion.get("supplier_risk_score", 0),
            "quality_score": suggestion.get("quality_score", 0),
            "robustness_score": suggestion.get("robustness_score", 0),
            "overall_score": suggestion.get("overall_score", 0),
        }
