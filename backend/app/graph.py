from __future__ import annotations

import uuid
from typing import List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langsmith import traceable

from app.agents.supervisor import SupervisorAgent
from app.agents.recovery_recommendation import RecoveryRecommendationAgent
from app.agents.verification_replanning import VerificationReplanningAgent
from app.db.session import get_session_factory
from app.services.workflow_service import WorkflowService
import app.db.models.materials
import app.db.models.suppliers
import app.db.models.inventory
import app.db.models.production
import app.db.models.procurement
import app.db.models.risk
import app.db.models.workflow
import app.db.models.contract_models


class DisruptionState(TypedDict):
    incident_id: str
    incident_type: str
    material_id: str
    po_id: Optional[str]
    supplier_id: Optional[str]
    description: str
    severity: str
    risk_report: Optional[dict]
    eligible_suppliers: List[dict]
    proposed_plans: List[dict]
    selected_plan: Optional[dict]
    validation_results: List[dict]
    simulation_results: List[dict]
    verification_status: Optional[dict]
    approval_id: Optional[str]
    status: str
    logs: List[str]


supervisor_agent = SupervisorAgent()
recovery_agent = RecoveryRecommendationAgent()
verification_agent = VerificationReplanningAgent()
workflow_service = WorkflowService()


@traceable(name="Supervisor Node (Incident Analysis)")
async def supervisor_node(state: DisruptionState) -> dict:
    """Analyze risk and evaluate suppliers using the live database."""
    logs = list(state.get("logs") or [])
    logs.append("Supervisor Node: Registering incident and analyzing risk...")

    material_id = state.get("material_id")
    if not material_id:
        raise ValueError("material_id is required for database-backed graph execution")

    factory = get_session_factory()
    async with factory() as session:
        workflow_state = await supervisor_agent.start_workflow(
            session,
            {
                "incident_type": state.get("incident_type", "STOCKOUT_RISK"),
                "material_id": material_id,
                "po_id": state.get("po_id"),
                "supplier_id": state.get("supplier_id"),
                "description": state.get("description", ""),
                "severity": state.get("severity", "MEDIUM"),
            },
        )

    analysis = workflow_state.get("analysis", {})
    risk_data = analysis.get("risk_report") or {}
    suppliers_data = analysis.get("eligible_suppliers") or []
    incident_id = workflow_state["incident_id"]
    logs.append(
        f"Supervisor Node: Risk evaluated as {risk_data.get('risk_level', 'UNKNOWN')}. "
        f"{len(suppliers_data)} candidate suppliers analyzed."
    )

    return {
        "incident_id": incident_id,
        "risk_report": risk_data,
        "eligible_suppliers": suppliers_data,
        "status": "ANALYZED",
        "logs": logs,
    }


@traceable(name="Recovery Agent Node (Plan Generation)")
async def recovery_node(state: DisruptionState) -> dict:
    """Generate multi-sourcing and emergency recovery strategies."""
    logs = list(state.get("logs") or [])
    logs.append("Recovery Node: Formulating recovery strategies and split sourcing options...")

    incident_id = state.get("incident_id")
    if not incident_id:
        raise ValueError("incident_id is required for recovery")

    factory = get_session_factory()
    async with factory() as session:
        plans = await recovery_agent.generate_plans(session, incident_id)

    plans = [{**plan, "status": plan.get("status", "PROPOSED")} for plan in plans]
    selected_plan = max(plans, key=lambda plan: plan.get("overall_score", 0)) if plans else None

    logs.append(f"Recovery Node: Generated {len(plans)} feasible recovery plans.")

    return {
        "proposed_plans": plans,
        "selected_plan": selected_plan,
        "status": "RECOMMENDED",
        "logs": logs,
    }


@traceable(name="Validation & Simulation Node (What-If Stress Test)")
async def validation_simulation_node(state: DisruptionState) -> dict:
    """Stress test recovery plans deterministically against safety stock & lead time constraints."""
    logs = list(state.get("logs") or [])
    logs.append("Validation & Simulation Node: Running What-If stress test under +2d delay assumption...")

    plans = state.get("proposed_plans") or []
    val_results = []
    sim_results = []

    factory = get_session_factory()
    async with factory() as session:
        for plan in plans:
            plan_dict = recovery_agent._suggestion_to_plan_dict(
                state["incident_id"], plan
            )
            plan_dict["material_id"] = state.get("material_id")
            validation_report = await recovery_agent.validation_engine.validate_plan(
                session, plan_dict
            )
            val_results.append({
                "plan_id": plan["plan_id"],
                "valid": validation_report.valid,
                "violations": validation_report.violations,
                "warnings": validation_report.warnings,
            })

            if plan_dict.get("supplier_id"):
                sim_result = await recovery_agent.simulation_engine.simulate_plan(
                    session, plan_dict
                )
                sim_results.append({
                    "plan_id": plan["plan_id"],
                    "feasible": sim_result.feasible,
                    "coverage_after_recovery": float(sim_result.production_coverage_days),
                    "production_stop_avoided": sim_result.production_stop_avoided,
                    "remaining_risk": sim_result.remaining_risk_level,
                })
            else:
                sim_results.append({
                    "plan_id": plan["plan_id"],
                    "feasible": False,
                    "coverage_after_recovery": 0.0,
                    "production_stop_avoided": False,
                    "remaining_risk": "UNKNOWN",
                })

    passed = sum(1 for result in val_results if result["valid"])
    logs.append(
        f"Validation & Simulation Node: {passed}/{len(plans)} plans passed deterministic checks."
    )

    return {
        "validation_results": val_results,
        "simulation_results": sim_results,
        "status": "VALIDATED",
        "logs": logs,
    }


@traceable(name="Verification Node (Goal Verification)")
async def verification_node(state: DisruptionState) -> dict:
    """Verify continuity objectives and log final state snapshot."""
    logs = list(state.get("logs") or [])
    logs.append("Verification Node: Verifying 7-day minimum stock coverage objective...")

    selected = state.get("selected_plan") or {}
    if not selected.get("plan_id"):
        ver_status = {
            "verified": False,
            "reason": "No recovery plan was generated",
            "needs_replan": False,
        }
    else:
        factory = get_session_factory()
        async with factory() as session:
            ver_status = await verification_agent.verify_execution(
                session, selected["plan_id"]
            )

    logs.append(
        "Verification Node: "
        + ("Plan status checked." if ver_status.get("reason") else "Verification completed.")
    )

    return {
        "verification_status": ver_status,
        "status": "AWAITING_APPROVAL",
        "logs": logs,
    }


@traceable(name="Human Approval Gate")
async def approval_gate_node(state: DisruptionState) -> dict:
    """Persist a pending approval and stop before any operational mutation."""
    valid_plan_ids = {
        result["plan_id"]
        for result in state.get("validation_results") or []
        if result.get("valid")
    }
    selected = state.get("selected_plan") or {}
    if selected.get("plan_id") not in valid_plan_ids:
        selected = next(
            (plan for plan in state.get("proposed_plans") or []
             if plan.get("plan_id") in valid_plan_ids),
            None,
        )
    if not selected:
        return {
            "approval_id": None,
            "status": "BLOCKED_INVALID_PLAN",
            "logs": list(state.get("logs") or []) + [
                "Human Approval Gate: No valid plan available for approval."
            ],
        }

    factory = get_session_factory()
    async with factory() as session:
        approval = await workflow_service.request_plan_approval(
            session, selected["plan_id"]
        )
    return {
        "selected_plan": selected,
        "approval_id": approval.approval_id,
        "status": "AWAITING_APPROVAL",
        "logs": list(state.get("logs") or []) + [
            f"Human Approval Gate: Approval {approval.approval_id} is pending."
        ],
    }


# Construct StateGraph
builder = StateGraph(DisruptionState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("recovery", recovery_node)
builder.add_node("validation_simulation", validation_simulation_node)
builder.add_node("approval_gate", approval_gate_node)

builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "recovery")
builder.add_edge("recovery", "validation_simulation")
builder.add_edge("validation_simulation", "approval_gate")
builder.add_edge("approval_gate", END)

# Export compiled graph for LangGraph Studio & LangSmith
graph = builder.compile()
