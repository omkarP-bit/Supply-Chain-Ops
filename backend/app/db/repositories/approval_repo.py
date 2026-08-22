from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow import ApprovalRequest

async def create_approval(session: AsyncSession, **kwargs) -> ApprovalRequest:
    approval = ApprovalRequest(**kwargs)
    session.add(approval)
    await session.flush()
    await session.commit()
    return approval

async def get_approval(session: AsyncSession, approval_id: str) -> ApprovalRequest | None:
    return (await session.execute(
        select(ApprovalRequest).where(ApprovalRequest.approval_id == approval_id)
    )).scalar_one_or_none()

async def list_pending_approvals(session: AsyncSession) -> list[ApprovalRequest]:
    q = (
        select(ApprovalRequest)
        .where(ApprovalRequest.status == "PENDING")
        .order_by(ApprovalRequest.requested_at.asc())
    )
    return list((await session.execute(q)).scalars())

async def update_approval_decision(
    session: AsyncSession, approval_id: str, status: str, approved_by: str, reason: str | None = None
) -> ApprovalRequest | None:
    approval = await get_approval(session, approval_id)
    if approval:
        approval.status = status
        approval.approved_by = approved_by
        approval.decision_at = datetime.now(timezone.utc)
        approval.decision_reason = reason
        await session.flush()
        await session.commit()
    return approval
