from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import approval_repo, audit_repo
from app.schemas.approval import ApprovalResponse, ApprovalDecision

router = APIRouter(prefix="/api/v1", tags=["approvals"])


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
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval is already {approval.status}")

    updated = await approval_repo.update_approval_decision(
        db, approval_id, status="APPROVED", approved_by="system"
    )

    await audit_repo.create_audit_event(
        db,
        incident_id=approval.incident_id,
        agent_name="approval_agent",
        event_type="APPROVAL",
        action="APPROVE",
        input_data={"approval_id": approval_id},
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
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval is already {approval.status}")

    updated = await approval_repo.update_approval_decision(
        db, approval_id, status="REJECTED", approved_by="system", reason=decision.reason
    )

    await audit_repo.create_audit_event(
        db,
        incident_id=approval.incident_id,
        agent_name="approval_agent",
        event_type="APPROVAL",
        action="REJECT",
        input_data={"approval_id": approval_id, "reason": decision.reason},
        output_data={"status": "REJECTED"},
        risk_level=None,
    )

    return updated
