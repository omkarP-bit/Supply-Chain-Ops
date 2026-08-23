from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import incident_repo, audit_repo
from app.engines.risk_engine import OperationalRiskEngine
from app.engines.supplier_engine import SupplierEvaluationEngine


class SupervisorAgent:

    def __init__(self):
        self.risk_engine = OperationalRiskEngine()
        self.supplier_engine = SupplierEvaluationEngine()

    async def start_workflow(
        self, session: AsyncSession, incident_data: dict
    ) -> dict:
        incident_id = str(uuid.uuid4().hex[:16])
        material_id = incident_data.get("material_id")

        incident = await incident_repo.create_incident(
            session,
            incident_id=incident_id,
            incident_type=incident_data.get("incident_type", "STOCKOUT_RISK"),
            material_id=material_id,
            po_id=incident_data.get("po_id"),
            supplier_id=incident_data.get("supplier_id"),
            description=incident_data.get("description", ""),
            severity=incident_data.get("severity", "MEDIUM"),
            status="ANALYZING",
        )

        await audit_repo.create_audit_event(
            session,
            incident_id=incident_id,
            agent_name="SupervisorAgent",
            event_type="INCIDENT_CREATED",
            action="incident_registered",
            input_data=incident_data,
            output_data={"incident_id": incident_id, "status": "ANALYZING"},
        )

        risk_report = None
        eligible_suppliers: list[dict] = []

        if material_id:
            report = await self.risk_engine.calculate_risk(session, material_id)
            risk_report = {
                "material_id": str(report.material_id),
                "risk_level": report.risk_level,
                "usable_stock": float(report.usable_stock),
                "avg_daily_consumption_30d": float(report.avg_daily_consumption_30d),
                "avg_daily_consumption_7d": float(report.avg_daily_consumption_7d),
                "coverage_days": float(report.coverage_days),
                "inventory_discrepancy": float(report.inventory_discrepancy),
                "discrepancy_percentage": float(report.discrepancy_percentage),
                "erp_quantity": float(report.erp_quantity),
                "physical_quantity": float(report.physical_quantity),
                "hours_to_production_stop": report.hours_to_production_stop,
                "affected_orders": len(report.affected_orders),
                "trend_7d_vs_30d": report.trend_7d_vs_30d,
                "threshold_violations": report.threshold_violations,
            }

            candidates = await self.supplier_engine.get_supplier_candidates(
                session,
                material_id,
                required_quantity=(
                    abs(report.inventory_discrepancy)
                    if report.inventory_discrepancy < 0
                    else report.usable_stock
                ),
            )
            eligible_suppliers = [
                {
                    "supplier_id": str(c.supplier_id),
                    "supplier_name": c.supplier_name,
                    "available_quantity": float(c.available_quantity),
                    "unit_price": float(c.unit_price),
                    "currency": c.currency,
                    "lead_time_days": c.lead_time_days,
                    "certification_valid": c.certification_valid,
                    "aql_level": c.aql_level,
                    "material_grade": c.material_grade,
                    "quality_score": float(c.quality_score),
                    "reliability_score": float(c.reliability_score),
                    "on_time_delivery_rate": float(c.on_time_delivery_rate),
                    "score": float(c.score),
                    "rejection_reason": c.rejection_reason,
                }
                for c in candidates
            ]

        workflow_state = {
            "incident_id": incident_id,
            "risk_level": risk_report.get("risk_level", "UNKNOWN") if risk_report else "UNKNOWN",
            "analysis": {
                "risk_report": risk_report,
                "eligible_suppliers": eligible_suppliers,
            },
            "status": "ANALYZING",
        }

        incident.workflow_state = workflow_state
        await session.flush()
        await session.commit()

        return workflow_state
