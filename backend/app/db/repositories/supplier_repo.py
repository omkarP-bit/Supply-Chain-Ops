from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.suppliers import Supplier, SupplierMaterial, SupplierPerformance

async def get_supplier(session: AsyncSession, supplier_id: str) -> Supplier | None:
    return (await session.execute(select(Supplier).where(Supplier.supplier_id == supplier_id))).scalar_one_or_none()

async def list_active_suppliers(session: AsyncSession) -> list[Supplier]:
    q = select(Supplier).where(Supplier.status == "ACTIVE").order_by(Supplier.supplier_name)
    return list((await session.execute(q)).scalars())

async def get_supplier_material(session: AsyncSession, supplier_id: str, material_id: str) -> SupplierMaterial | None:
    q = select(SupplierMaterial).where(
        SupplierMaterial.supplier_id == supplier_id,
        SupplierMaterial.material_id == material_id,
    )
    return (await session.execute(q)).scalar_one_or_none()

async def get_supplier_candidates_for_material(session: AsyncSession, material_id: str) -> list[Supplier]:
    q = (
        select(Supplier)
        .join(SupplierMaterial, SupplierMaterial.supplier_id == Supplier.supplier_id)
        .where(SupplierMaterial.material_id == material_id, Supplier.status == "ACTIVE")
        .order_by(Supplier.overall_reliability_score.desc())
    )
    return list((await session.execute(q)).scalars())

async def get_supplier_performance(session: AsyncSession, supplier_id: str) -> list[SupplierPerformance]:
    q = (
        select(SupplierPerformance)
        .where(SupplierPerformance.supplier_id == supplier_id)
        .order_by(SupplierPerformance.evaluation_date.desc())
    )
    return list((await session.execute(q)).scalars())

async def count_active_suppliers(session: AsyncSession) -> int:
    return (await session.execute(
        select(func.count()).select_from(Supplier).where(Supplier.status == "ACTIVE")
    )).scalar()
