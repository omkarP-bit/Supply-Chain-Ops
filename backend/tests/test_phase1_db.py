import asyncio
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings

_seed_done = False


async def _run_test(coro_func):
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        global _seed_done
        if not _seed_done:
            from app.db.seed import seed_db
            async with factory() as session:
                await seed_db(session)
            _seed_done = True
        async with factory() as session:
            return await coro_func(session)
    finally:
        await engine.dispose()


def _run(coro_func):
    asyncio.run(_run_test(coro_func))


class TestDatabaseSchema:
    def test_materials_table_exists(self):
        async def _check(session):
            r = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='materials')")
            )
            assert r.scalar()
        _run(_check)

    def test_comp104_seeded(self):
        async def _check(session):
            from app.db.models.materials import Material
            m = (await session.execute(
                select(Material).where(Material.material_id == "COMP-104")
            )).scalar_one_or_none()
            assert m is not None
            assert m.material_name == "Precision Aluminum Housing"
            assert m.criticality_level == "CRITICAL"
        _run(_check)

    def test_material_spec_seeded(self):
        async def _check(session):
            from app.db.models.materials import MaterialSpecification
            s = (await session.execute(
                select(MaterialSpecification).where(MaterialSpecification.material_id == "COMP-104")
            )).scalar_one_or_none()
            assert s is not None
            assert s.material_grade == "AL-6061-T6"
        _run(_check)

    def test_at_least_3_materials(self):
        async def _check(session):
            from app.db.models.materials import Material
            r = await session.execute(select(func.count()).select_from(Material))
            assert r.scalar() >= 3
        _run(_check)


class TestSupplierSeeding:
    def test_sup21_seeded(self):
        async def _check(session):
            from app.db.models.suppliers import Supplier
            s = (await session.execute(
                select(Supplier).where(Supplier.supplier_id == "SUP-21")
            )).scalar_one_or_none()
            assert s is not None
            assert s.supplier_name == "Budget Metals Co"
            assert s.risk_level == "HIGH"
        _run(_check)

    def test_sup34_reliability(self):
        async def _check(session):
            from app.db.models.suppliers import Supplier
            s = (await session.execute(
                select(Supplier).where(Supplier.supplier_id == "SUP-34")
            )).scalar_one_or_none()
            assert s.overall_reliability_score == Decimal("94")
        _run(_check)

    def test_sup77_inactive(self):
        async def _check(session):
            from app.db.models.suppliers import Supplier
            s = (await session.execute(
                select(Supplier).where(Supplier.supplier_id == "SUP-77")
            )).scalar_one_or_none()
            assert s.status == "INACTIVE"
        _run(_check)

    def test_4_supplier_materials(self):
        async def _check(session):
            from app.db.models.suppliers import SupplierMaterial
            r = await session.execute(
                select(func.count()).select_from(SupplierMaterial)
                .where(SupplierMaterial.material_id == "COMP-104")
            )
            assert r.scalar() == 4
        _run(_check)

    def test_sup21_cert_invalid(self):
        async def _check(session):
            from app.db.models.suppliers import SupplierMaterial
            sm = (await session.execute(
                select(SupplierMaterial).where(
                    SupplierMaterial.supplier_id == "SUP-21",
                    SupplierMaterial.material_id == "COMP-104"
                )
            )).scalar_one_or_none()
            assert sm.certification_valid is False
        _run(_check)

    def test_sup34_cert_valid(self):
        async def _check(session):
            from app.db.models.suppliers import SupplierMaterial
            sm = (await session.execute(
                select(SupplierMaterial).where(
                    SupplierMaterial.supplier_id == "SUP-34",
                    SupplierMaterial.material_id == "COMP-104"
                )
            )).scalar_one_or_none()
            assert sm.certification_valid is True
        _run(_check)

    def test_sup52_insufficient_stock(self):
        async def _check(session):
            from app.db.models.suppliers import SupplierMaterial
            sm = (await session.execute(
                select(SupplierMaterial).where(
                    SupplierMaterial.supplier_id == "SUP-52",
                    SupplierMaterial.material_id == "COMP-104"
                )
            )).scalar_one_or_none()
            assert sm.available_quantity == Decimal("100")
        _run(_check)


class TestInventorySeeding:
    def test_35_snapshots(self):
        async def _check(session):
            from app.db.models.inventory import InventorySnapshot
            r = await session.execute(
                select(func.count()).select_from(InventorySnapshot)
                .where(InventorySnapshot.material_id == "COMP-104")
            )
            assert r.scalar() == 35
        _run(_check)

    def test_today_stale_inventory(self):
        async def _check(session):
            from app.db.models.inventory import InventorySnapshot
            s = (await session.execute(
                select(InventorySnapshot)
                .where(InventorySnapshot.material_id == "COMP-104")
                .order_by(InventorySnapshot.snapshot_date.desc())
                .limit(1)
            )).scalar_one_or_none()
            assert s.erp_quantity == Decimal("800")
            assert s.physical_quantity == Decimal("390")
            assert s.usable_quantity == Decimal("390")
        _run(_check)

    def test_discrepancy_percentage(self):
        async def _check(session):
            from app.db.models.inventory import InventorySnapshot
            s = (await session.execute(
                select(InventorySnapshot)
                .where(InventorySnapshot.material_id == "COMP-104")
                .order_by(InventorySnapshot.snapshot_date.desc())
                .limit(1)
            )).scalar_one_or_none()
            pct = abs(float(s.erp_quantity) - float(s.physical_quantity)) / float(s.erp_quantity) * 100
            assert 51.0 < pct < 52.0
        _run(_check)


class TestProductionOrders:
    def test_prod882_critical(self):
        async def _check(session):
            from app.db.models.production import ProductionOrder
            p = (await session.execute(
                select(ProductionOrder).where(ProductionOrder.production_order_id == "PROD-882")
            )).scalar_one_or_none()
            assert p is not None
            assert p.priority == 1
            assert p.status == "IN_PROGRESS"
            assert p.remaining_quantity == Decimal("1050")
        _run(_check)


class TestPurchaseOrder:
    def test_po7712_delayed(self):
        async def _check(session):
            from app.db.models.procurement import PurchaseOrder
            po = (await session.execute(
                select(PurchaseOrder).where(PurchaseOrder.po_id == "PO-7712")
            )).scalar_one_or_none()
            assert po is not None
            assert po.supplier_id == "SUP-21"
            assert po.status == "DELAYED"
            assert po.total_cost == Decimal("84000")
        _run(_check)


class TestRiskThresholds:
    def test_3_thresholds(self):
        async def _check(session):
            from app.db.models.risk import RiskThreshold
            r = await session.execute(
                select(func.count()).select_from(RiskThreshold)
                .where(RiskThreshold.material_id == "COMP-104")
            )
            assert r.scalar() == 3
        _run(_check)
