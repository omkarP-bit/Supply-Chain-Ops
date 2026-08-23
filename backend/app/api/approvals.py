import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import approval_repo, audit_repo, incident_repo, recovery_repo
from app.schemas.approval import ApprovalResponse, ApprovalDecision, ExecutionCommand
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/v1", tags=["approvals"])
workflow_service = WorkflowService()


@router.post("/plans/{plan_id}/approval", response_model=ApprovalResponse, status_code=201)
async def request_plan_approval(plan_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await workflow_service.request_plan_approval(db, plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/plans/{plan_id}/execute")
async def execute_plan(plan_id: str, command: ExecutionCommand, db: AsyncSession = Depends(get_db)):
    if command.plan_id != plan_id:
        raise HTTPException(status_code=422, detail="Path plan_id does not match command plan_id")
    try:
        return await workflow_service.execute_plan(db, command.plan_id, command.approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/plans/{plan_id}/verify")
async def verify_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger deterministic post-execution verification on a plan."""
    return await workflow_service.verify_plan(db, plan_id)


@router.get("/approvals", response_model=list[ApprovalResponse])
async def list_pending_approvals(db: AsyncSession = Depends(get_db)):
    return await approval_repo.list_pending_approvals(db)


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
):
    approval = await approval_repo.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_request(
    approval_id: str,
    db: AsyncSession = Depends(get_db),
):
    approval = await approval_repo.get_approval(db, approval_id)
    if not approval:
        # Fallback check by incident_id or plan_id
        pending_list = await approval_repo.list_pending_approvals(db)
        approval = next((a for a in pending_list if a.incident_id == approval_id or a.plan_id == approval_id), None)

    if not approval:
        # Fallback check directly in incident or plan repositories to create on-demand
        inc = await incident_repo.get_incident(db, approval_id)
        plan = None
        if inc:
            plans = await recovery_repo.list_plans_for_incident(db, inc.incident_id)
            if plans:
                plan = plans[0]
        else:
            plan = await recovery_repo.get_plan(db, approval_id)
            if plan:
                inc = await incident_repo.get_incident(db, plan.incident_id)

        if inc or plan:
            inc_id = inc.incident_id if inc else plan.incident_id
            p_id = plan.plan_id if plan else uuid.uuid4().hex[:16]
            cost = plan.estimated_cost if plan else Decimal("12000.00")
            approval = await approval_repo.create_approval(
                db,
                approval_id=uuid.uuid4().hex[:16],
                incident_id=inc_id,
                plan_id=p_id,
                requested_amount=cost,
                approval_threshold=Decimal("75000.00"),
                production_impact=f"Estimated impact: {plan.production_impact_hours if plan else 0} hours",
                risk_if_rejected="Disruption risk remains if rejected",
                alternatives_considered=[{"plan_name": plan.plan_name if plan else "Standard Recovery"}],
                status="PENDING",
            )

    if not approval:
        # Check if already approved
        raise HTTPException(status_code=404, detail="Approval request not found or already concluded")

    if approval.status == "APPROVED":
        return approval

    updated = await approval_repo.update_approval_decision(
        db, approval.approval_id, status="APPROVED", approved_by="Operations Manager"
    )

    if approval.incident_id:
        inc = await incident_repo.get_incident(db, approval.incident_id)
        if inc:
            inc.status = "APPROVED"
            if inc.workflow_state and isinstance(inc.workflow_state, dict):
                inc.workflow_state["workflow_stage"] = "EXECUTE"
            await incident_repo.update_incident_status(db, approval.incident_id, "APPROVED")

    await audit_repo.create_audit_event(
        db,
        incident_id=approval.incident_id,
        agent_name="approval_agent",
        event_type="APPROVAL",
        action="APPROVE",
        input_data={"approval_id": approval.approval_id},
        output_data={"status": "APPROVED", "approved_by": "Operations Manager"},
        risk_level=None,
    )

    return updated


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_request(
    approval_id: str,
    decision: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
):
    approval = await approval_repo.get_approval(db, approval_id)
    if not approval:
        pending_list = await approval_repo.list_pending_approvals(db)
        approval = next((a for a in pending_list if a.incident_id == approval_id or a.plan_id == approval_id), None)

    if not approval:
        # Fallback check directly in incident or plan repositories to create on-demand
        inc = await incident_repo.get_incident(db, approval_id)
        plan = None
        if inc:
            plans = await recovery_repo.list_plans_for_incident(db, inc.incident_id)
            if plans:
                plan = plans[0]
        else:
            plan = await recovery_repo.get_plan(db, approval_id)
            if plan:
                inc = await incident_repo.get_incident(db, plan.incident_id)

        if inc or plan:
            inc_id = inc.incident_id if inc else plan.incident_id
            p_id = plan.plan_id if plan else uuid.uuid4().hex[:16]
            cost = plan.estimated_cost if plan else Decimal("12000.00")
            approval = await approval_repo.create_approval(
                db,
                approval_id=uuid.uuid4().hex[:16],
                incident_id=inc_id,
                plan_id=p_id,
                requested_amount=cost,
                approval_threshold=Decimal("75000.00"),
                production_impact=f"Estimated impact: {plan.production_impact_hours if plan else 0} hours",
                risk_if_rejected="Disruption risk remains if rejected",
                alternatives_considered=[{"plan_name": plan.plan_name if plan else "Standard Recovery"}],
                status="PENDING",
            )

    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found or already concluded")

    if approval.status == "REJECTED":
        return approval

    updated = await approval_repo.update_approval_decision(
        db, approval.approval_id, status="REJECTED", approved_by="Operations Manager", reason=decision.reason
    )

    if approval.incident_id:
        await incident_repo.update_incident_status(db, approval.incident_id, "REPLANNING")

    await audit_repo.create_audit_event(
        db,
        incident_id=approval.incident_id,
        agent_name="approval_agent",
        event_type="APPROVAL",
        action="REJECT",
        input_data={"approval_id": approval.approval_id},
        output_data={"status": "REJECTED", "approved_by": "Operations Manager", "reason": decision.reason},
        risk_level=None,
    )

    return updated
