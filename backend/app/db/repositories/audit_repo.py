from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow import AuditEvent

async def create_audit_event(session: AsyncSession, **kwargs) -> AuditEvent:
    event = AuditEvent(**kwargs)
    session.add(event)
    await session.flush()
    await session.commit()
    return event

async def get_audit_events_for_incident(session: AsyncSession, incident_id: str) -> list[AuditEvent]:
    q = (
        select(AuditEvent)
        .where(AuditEvent.incident_id == incident_id)
        .order_by(AuditEvent.timestamp.asc())
    )
    return list((await session.execute(q)).scalars())
