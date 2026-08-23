from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import approval_repo, audit_repo
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
        # Check if already approved
        raise HTTPException(status_code=404, detail="Approval request not found or already concluded")

    if approval.status == "APPROVED":
        return approval

    updated = await approval_repo.update_approval_decision(
        db, approval.approval_id, status="APPROVED", approved_by="system"
    )

    await audit_repo.create_audit_event(
        db,
        incident_id=approval.incident_id,
        agent_name="approval_agent",
        event_type="APPROVAL",
        action="APPROVE",
        input_data={"approval_id": approval.approval_id},
        output_data={"status": "APPROVED"},
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
        raise HTTPException(status_code=404, detail="Approval request not found or already concluded")

    if approval.status == "REJECTED":
        return approval

    updated = await approval_repo.update_approval_decision(
        db, approval.approval_id, status="REJECTED", approved_by="system", reason=decision.reason
    )

    await audit_repo.create_audit_event(
        db,
        incident_id=approval.incident_id,
        agent_name="approval_agent",
        event_type="APPROVAL",
        action="REJECT",
        input_data={"approval_id": approval.approval_id, "reason": decision.reason},
        output_data={"status": "REJECTED"},
        risk_level=None,
    )

    return updated
