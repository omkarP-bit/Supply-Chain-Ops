from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.workflow import RecoveryPlan

async def create_plan(session: AsyncSession, **kwargs) -> RecoveryPlan:
    plan = RecoveryPlan(**kwargs)
    session.add(plan)
    await session.flush()
    await session.commit()
    return plan

async def get_plan(session: AsyncSession, plan_id: str) -> RecoveryPlan | None:
    return (await session.execute(
        select(RecoveryPlan).where(RecoveryPlan.plan_id == plan_id)
    )).scalar_one_or_none()

async def list_plans_for_incident(session: AsyncSession, incident_id: str) -> list[RecoveryPlan]:
    q = (
        select(RecoveryPlan)
        .where(RecoveryPlan.incident_id == incident_id)
        .order_by(RecoveryPlan.overall_score.desc())
    )
    return list((await session.execute(q)).scalars())

async def update_plan_status(session: AsyncSession, plan_id: str, status: str) -> RecoveryPlan | None:
    plan = await get_plan(session, plan_id)
    if plan:
        plan.status = status
        await session.flush()
        await session.commit()
    return plan
