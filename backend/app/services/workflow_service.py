from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import SupervisorAgent
from app.agents.recovery_recommendation import RecoveryRecommendationAgent
from app.agents.verification_replanning import VerificationReplanningAgent
from app.db.repositories import incident_repo, recovery_repo, approval_repo, audit_repo
from app.audit.audit_service import log_event


class WorkflowService:

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.recovery_agent = RecoveryRecommendationAgent()
        self.verification_agent = VerificationReplanningAgent()

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
        plan = await recovery_repo.get_plan(session, plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        approval = await approval_repo.get_approval(session, approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        if approval.status != "APPROVED":
            raise ValueError(f"Approval {approval_id} is not approved (status={approval.status})")

        await log_event(
            session,
            incident_id=plan.incident_id,
            agent_name="WorkflowService",
            event_type="EXECUTION_STARTED",
            action="plan_execution",
            input_data={"plan_id": plan_id, "approval_id": approval_id},
        )

        po_id = str(uuid.uuid4().hex[:16])
        plan_details = plan.plan_details or {}

        await recovery_repo.update_plan_status(session, plan_id, "EXECUTING")

        await audit_repo.create_audit_event(
            session,
            incident_id=plan.incident_id,
            agent_name="WorkflowService",
            event_type="PO_CREATED",
            action="purchase_order_created",
            input_data={"plan_id": plan_id},
            output_data={"po_id": po_id, "status": "CONFIRMED"},
        )

        await recovery_repo.update_plan_status(session, plan_id, "COMPLETED")

        await log_event(
            session,
            incident_id=plan.incident_id,
            agent_name="WorkflowService",
            event_type="EXECUTION_COMPLETED",
            action="plan_execution",
            output_data={"plan_id": plan_id, "po_id": po_id, "final_status": "COMPLETED"},
        )

        return {
            "plan_id": plan_id,
            "po_id": po_id,
            "status": "COMPLETED",
            "incident_id": plan.incident_id,
        }
