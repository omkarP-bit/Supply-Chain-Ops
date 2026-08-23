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
    session: AsyncSession, *, status: str | None = None, skip: int = 0, limit: int = 50, dedup_by_material: bool = True
) -> list[Incident]:
    q = select(Incident)
    if status:
        q = q.where(Incident.status == status)
    q = q.order_by(Incident.created_at.desc())
    res = await session.execute(q)
    all_incs = list(res.scalars().all())
    
    if dedup_by_material:
        seen = set()
        deduped = []
        for inc in all_incs:
            mat = inc.material_id or inc.incident_id
            if mat not in seen:
                seen.add(mat)
                deduped.append(inc)
        return deduped[skip : skip + limit]
    
    return all_incs[skip : skip + limit]

async def update_incident_status(session: AsyncSession, incident_id: str, status: str) -> Incident | None:
    incident = await get_incident(session, incident_id)
    if incident:
        incident.status = status
        await session.flush()
        await session.commit()
    return incident
