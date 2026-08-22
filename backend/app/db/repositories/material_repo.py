from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.materials import Material, MaterialSpecification

async def get_material(session: AsyncSession, material_id: str) -> Material | None:
    return (await session.execute(select(Material).where(Material.material_id == material_id))).scalar_one_or_none()

async def list_materials(session: AsyncSession, skip=0, limit=50) -> list[Material]:
    return list((await session.execute(select(Material).offset(skip).limit(limit))).scalars())

async def get_material_spec(session: AsyncSession, material_id: str) -> MaterialSpecification | None:
    return (await session.execute(select(MaterialSpecification).where(MaterialSpecification.material_id == material_id))).scalar_one_or_none()

async def count_materials(session: AsyncSession) -> int:
    from sqlalchemy import func
    return (await session.execute(select(func.count()).select_from(Material))).scalar()
