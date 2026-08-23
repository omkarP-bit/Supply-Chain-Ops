from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import SupervisorAgent
from app.agents.recovery_recommendation import RecoveryRecommendationAgent
from app.agents.verification_replanning import VerificationReplanningAgent
from app.db.repositories import incident_repo, recovery_repo, approval_repo, audit_repo
from app.audit.audit_service import log_event
from app.config import settings
from app.engines.validation_engine import PlanValidationEngine
from app.schemas.approval import ExecutionCommand
from app.tools.purchase_order_tools import create_purchase_order


class WorkflowService:

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.recovery_agent = RecoveryRecommendationAgent()
        self.verification_agent = VerificationReplanningAgent()
        self.validation_engine = PlanValidationEngine()

    async def request_plan_approval(
        self, session: AsyncSession, plan_id: str
    ):
        plan = await recovery_repo.get_plan(session, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        details = plan.plan_details or {}
        plan_dict = {
            "plan_id": plan.plan_id,
            "material_id": details.get("material_id"),
            "supplier_id": details.get("supplier_id"),
            "required_quantity": details.get("quantity", 0) or details.get("required_quantity", 0),
            "unit_price": details.get("unit_price", 0),
            "total_cost": plan.estimated_cost,
            "deadline_days": details.get("lead_time_days") or details.get("deadline_days"),
            "allocations": details.get("allocations"),
            "plan_details": details,
        }
        validation = await self.validation_engine.validate_plan(session, plan_dict)
        if not validation.valid:
            raise ValueError(f"Plan {plan_id} failed deterministic validation")

        existing = await approval_repo.get_pending_approval_for_plan(session, plan_id)
        if existing:
            return existing

        approval = await approval_repo.create_approval(
            session,
            approval_id=uuid.uuid4().hex[:16],
            incident_id=plan.incident_id,
            plan_id=plan.plan_id,
            requested_amount=plan.estimated_cost,
            approval_threshold=Decimal(str(settings.approval_threshold_amount)),
            production_impact=f"Estimated production impact: {plan.production_impact_hours} hours",
            risk_if_rejected="Production disruption risk remains if this recovery plan is rejected",
            alternatives_considered=[{"plan_type": plan.plan_type, "plan_name": plan.plan_name}],
            status="PENDING",
        )
        await audit_repo.create_audit_event(
            session,
            incident_id=plan.incident_id,
            agent_name="WorkflowService",
            event_type="APPROVAL_REQUESTED",
            action="recovery_plan_approval_requested",
            input_data={"plan_id": plan_id, "amount": float(plan.estimated_cost)},
            output_data={"approval_id": approval.approval_id, "status": approval.status},
        )
        return approval

    async def analyze_incident(
        self, session: AsyncSession, incident_id: str
    ) -> dict:
        incident = await incident_repo.get_incident(session, incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        await log_event(
            session,
            incident_id=incident_id,
            agent_name="WorkflowService",
            event_type="ANALYSIS_STARTED",
            action="full_analysis_workflow",
        )

        state = await self.supervisor.start_workflow(
            session,
            {
                "incident_type": incident.incident_type,
                "material_id": incident.material_id,
                "po_id": incident.po_id,
                "supplier_id": incident.supplier_id,
                "description": incident.description,
                "severity": incident.severity,
            },
        )

        await log_event(
            session,
            incident_id=incident_id,
            agent_name="WorkflowService",
            event_type="ANALYSIS_COMPLETED",
            action="full_analysis_workflow",
            output_data={"risk_level": state.get("risk_level")},
        )

        return state

    async def recommend_recovery(
        self, session: AsyncSession, incident_id: str
    ) -> dict:
        incident = await incident_repo.get_incident(session, incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        await log_event(
            session,
            incident_id=incident_id,
            agent_name="WorkflowService",
            event_type="RECOMMENDATION_STARTED",
            action="recovery_recommendation_workflow",
        )

        result = await self.recovery_agent.recommend(session, incident_id)

        await log_event(
            session,
            incident_id=incident_id,
            agent_name="WorkflowService",
            event_type="RECOMMENDATION_COMPLETED",
            action="recovery_recommendation_workflow",
            output_data={
                "recommended_plan": result.get("recommended_plan"),
                "plan_count": len(result.get("plans", [])),
            },
        )

        return result

    async def execute_plan(
        self, session: AsyncSession, plan_id: str, approval_id: str
    ) -> dict:
        command = ExecutionCommand(plan_id=plan_id, approval_id=approval_id)
        plan = await recovery_repo.get_plan(session, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        approval = await approval_repo.get_approval(session, command.approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        if approval.status != "APPROVED" or approval.plan_id != plan.plan_id:
            raise ValueError(f"Approval {approval_id} is not approved (status={approval.status})")

        details = plan.plan_details or {}
        validation = await self.validation_engine.validate_plan(session, {
            "plan_id": plan.plan_id,
            "material_id": details.get("material_id"),
            "supplier_id": details.get("supplier_id"),
            "required_quantity": details.get("quantity", 0) or details.get("required_quantity", 0),
            "unit_price": details.get("unit_price", 0),
            "total_cost": plan.estimated_cost,
            "deadline_days": details.get("lead_time_days") or details.get("deadline_days"),
            "allocations": details.get("allocations"),
            "plan_details": details,
        })
        if not validation.valid:
            raise ValueError(f"Plan {plan_id} failed deterministic validation before execution")

        await log_event(
            session,
            incident_id=plan.incident_id,
            agent_name="WorkflowService",
            event_type="EXECUTION_STARTED",
            action="plan_execution",
            input_data={"plan_id": plan_id, "approval_id": approval_id},
        )

        await recovery_repo.update_plan_status(session, plan_id, "EXECUTING")

        supplier_id = details.get("supplier_id")
        material_id = details.get("material_id", "COMP-104")
        qty = Decimal(str(details.get("quantity", 0) or details.get("required_quantity", 0) or 0))
        unit_p = Decimal(str(details.get("unit_price", 0)))

        po_id = None
        if supplier_id and qty > 0:
            po_result = await create_purchase_order(
                session,
                supplier_id=supplier_id,
                material_id=material_id,
                quantity=qty,
                unit_price=unit_p,
            )
            po_id = po_result["po_id"]

            await audit_repo.create_audit_event(
                session,
                incident_id=plan.incident_id,
                agent_name="WorkflowService",
                event_type="PO_CREATED",
                action="purchase_order_created",
                input_data={"plan_id": plan_id},
                output_data=po_result,
            )

        await recovery_repo.update_plan_status(session, plan_id, "COMPLETED")
        await incident_repo.update_incident_status(session, plan.incident_id, "RESOLVED")

        # Automatically execute deterministic post-execution verification
        ver_result = await self.verification_agent.verify_execution(session, plan_id)

        await log_event(
            session,
            incident_id=plan.incident_id,
            agent_name="WorkflowService",
            event_type="EXECUTION_COMPLETED",
            action="plan_execution",
            output_data={
                "plan_id": plan_id,
                "po_id": po_id,
                "final_status": "COMPLETED",
                "verification_status": ver_result.get("verification_status"),
            },
        )

        return {
            "plan_id": plan_id,
            "po_id": po_id,
            "status": "COMPLETED",
            "incident_id": plan.incident_id,
            "verification": ver_result,
        }

    async def verify_plan(self, session: AsyncSession, plan_id: str) -> dict:
        """Explicitly verify plan execution against actual persisted operational state."""
        return await self.verification_agent.verify_execution(session, plan_id)
