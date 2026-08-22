from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow import Incident

async def create_incident(session: AsyncSession, **kwargs) -> Incident:
    incident = Incident(**kwargs)
    session.add(incident)
    await session.flush()
    await session.commit()
    return incident

async def get_incident(session: AsyncSession, incident_id: str) -> Incident | None:
    return (await session.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )).scalar_one_or_none()

async def list_incidents(
    session: AsyncSession, *, status: str | None = None, skip: int = 0, limit: int = 50
) -> list[Incident]:
    q = select(Incident)
    if status:
        q = q.where(Incident.status == status)
    q = q.order_by(Incident.created_at.desc()).offset(skip).limit(limit)
    return list((await session.execute(q)).scalars())

async def update_incident_status(session: AsyncSession, incident_id: str, status: str) -> Incident | None:
    incident = await get_incident(session, incident_id)
    if incident:
        incident.status = status
        await session.flush()
        await session.commit()
    return incident
