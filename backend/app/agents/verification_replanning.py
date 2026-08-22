from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import incident_repo, recovery_repo, audit_repo


class VerificationReplanningAgent:

    async def verify_execution(self, session: AsyncSession, plan_id: str) -> dict:
        plan = await recovery_repo.get_plan(session, plan_id)
        if not plan:
            return {"verified": False, "reason": "Plan not found", "needs_replan": False}

        incident = await incident_repo.get_incident(session, plan.incident_id)
        if not incident:
            return {"verified": False, "reason": "Incident not found", "needs_replan": False}

        state = incident.workflow_state or {}
        analysis = state.get("analysis", {})
        risk_report = analysis.get("risk_report") or {}

        expected_coverage = float(risk_report.get("coverage_days", 0))
        expected_hours = float(risk_report.get("hours_to_production_stop", 0))

        if plan.status == "EXECUTING":
            return {
                "verified": False,
                "reason": f"Plan '{plan.plan_id}' is still executing",
                "needs_replan": False,
            }

        if plan.status == "COMPLETED":
            objective_met = expected_coverage > 7 or expected_hours > 168
            return {
                "verified": objective_met,
                "reason": f"Plan completed. Coverage: {expected_coverage:.1f}d, Hours to stop: {expected_hours:.1f}h",
                "needs_replan": not objective_met,
            }

        if plan.status == "FAILED":
            return {
                "verified": False,
                "reason": f"Plan '{plan.plan_id}' failed",
                "needs_replan": True,
            }

        if plan.status == "INVALID":
            return {
                "verified": False,
                "reason": f"Plan '{plan.plan_id}' was invalid",
                "needs_replan": True,
            }

        return {
            "verified": False,
            "reason": f"Plan status is '{plan.status}', cannot determine outcome",
            "needs_replan": False,
        }

    async def trigger_replan(
        self, session: AsyncSession, incident_id: str, reason: str
    ) -> dict:
        incident = await incident_repo.update_incident_status(
            session, incident_id, "REPLANNING"
        )
        if not incident:
            return {"success": False, "reason": "Incident not found"}

        await audit_repo.create_audit_event(
            session,
            incident_id=incident_id,
            agent_name="VerificationReplanningAgent",
            event_type="REPLANNING_TRIGGERED",
            action="incident_replanning",
            reason=reason,
            output_data={"new_status": "REPLANNING"},
        )

        return {"success": True, "incident_id": incident_id, "status": "REPLANNING"}
