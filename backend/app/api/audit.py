from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.workflow import AuditEvent

router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/audit")
async def list_audit_events(
    limit: int = 100,
    incident_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(AuditEvent).order_by(desc(AuditEvent.timestamp)).limit(limit)
    if incident_id:
        q = q.where(AuditEvent.incident_id == incident_id)
    result = await db.execute(q)
    events = result.scalars().all()
    return [
        {
            "event_id": e.event_id,
            "incident_id": e.incident_id,
            "agent_name": e.agent_name,
            "event_type": e.event_type,
            "action": e.action,
            "input_data": e.input_data,
            "output_data": e.output_data,
            "reason": e.reason,
            "risk_level": e.risk_level,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "correlation_id": e.correlation_id,
        }
        for e in events
    ]
