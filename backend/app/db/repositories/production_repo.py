from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.production import ProductionOrder, ProductionConsumption

async def get_production_order(session: AsyncSession, production_order_id: str) -> ProductionOrder | None:
    return (await session.execute(
        select(ProductionOrder).where(ProductionOrder.production_order_id == production_order_id)
    )).scalar_one_or_none()

async def list_production_orders_for_material(session: AsyncSession, material_id: str) -> list[ProductionOrder]:
    q = (
        select(ProductionOrder)
        .join(ProductionConsumption, ProductionConsumption.production_order_id == ProductionOrder.production_order_id)
        .where(ProductionConsumption.material_id == material_id)
        .order_by(ProductionOrder.planned_start.desc())
    )
    return list((await session.execute(q)).scalars())

async def find_affected_orders(session: AsyncSession, material_id: str) -> list[ProductionOrder]:
    q = (
        select(ProductionOrder)
        .join(ProductionConsumption, ProductionConsumption.production_order_id == ProductionOrder.production_order_id)
        .where(
            ProductionConsumption.material_id == material_id,
            ProductionOrder.status.in_(["IN_PROGRESS", "PLANNED"]),
        )
        .order_by(ProductionOrder.planned_start.asc())
    )
    return list((await session.execute(q)).scalars())

async def count_at_risk(session: AsyncSession, material_id: str) -> int:
    from sqlalchemy import func
    q = (
        select(func.count())
        .select_from(ProductionOrder)
        .join(ProductionConsumption, ProductionConsumption.production_order_id == ProductionOrder.production_order_id)
        .where(
            ProductionConsumption.material_id == material_id,
            ProductionOrder.status.in_(["IN_PROGRESS", "PLANNED"]),
        )
    )
    return (await session.execute(q)).scalar()
