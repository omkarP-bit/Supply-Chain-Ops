import asyncio
import pytest
from decimal import Decimal

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


COMP_104 = "COMP-104"


class TestRiskEngineInventory:
    def test_get_current_inventory(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            snapshot = await engine.get_current_inventory(session, COMP_104)
            assert snapshot is not None
            assert snapshot.erp_quantity == Decimal("800")
            assert snapshot.physical_quantity == Decimal("390")
            assert snapshot.usable_quantity == Decimal("390")
        _run(_check)


class TestRiskEngineConsumption:
    def test_calculate_consumption_30d(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            avg = await engine.calculate_average_consumption_30d(session, COMP_104)
            assert avg > Decimal("0")
            assert avg < Decimal("100")
        _run(_check)

    def test_calculate_consumption_7d(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            avg_30d = await engine.calculate_average_consumption_30d(session, COMP_104)
            avg_7d = await engine.calculate_average_consumption_7d(session, COMP_104)
            assert avg_7d > Decimal("0")
            assert avg_7d > avg_30d
        _run(_check)


class TestRiskEngineCoverage:
    def test_calculate_coverage(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            result = await engine.calculate_inventory_coverage(session, COMP_104)
            coverage = result["coverage_days"]
            assert coverage > Decimal("0")
            assert coverage < Decimal("50")
        _run(_check)


class TestRiskEngineDiscrepancy:
    def test_calculate_discrepancy(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            result = await engine.calculate_inventory_discrepancy(session, COMP_104)
            disc_pct = result["discrepancy_percentage"]
            assert disc_pct > Decimal("51")
            assert disc_pct < Decimal("52")
        _run(_check)


class TestRiskEngineAffectedOrders:
    def test_find_affected_production_orders(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            orders = await engine.find_affected_production_orders(session, COMP_104)
            order_ids = [o.production_order_id for o in orders]
            assert "PROD-882" in order_ids
        _run(_check)


class TestRiskEngineHoursToStop:
    def test_hours_to_stop(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            hours = await engine.calculate_hours_to_production_stop(session, COMP_104)
            assert hours < 120.0
            assert hours > 0.0
        _run(_check)


class TestRiskEngineCalculateRisk:
    def test_calculate_risk(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            report = await engine.calculate_risk(session, COMP_104)
            assert report.risk_level == "CRITICAL"
            assert report.erp_quantity == Decimal("800")
            assert report.physical_quantity == Decimal("390")
            assert report.usable_stock == Decimal("390")
        _run(_check)

    def test_trend_accelerating(self):
        async def _check(session):
            from app.engines.risk_engine import OperationalRiskEngine
            engine = OperationalRiskEngine()
            report = await engine.calculate_risk(session, COMP_104)
            assert report.avg_daily_consumption_7d > report.avg_daily_consumption_30d
            assert "INCREASING" in report.trend_7d_vs_30d
        _run(_check)
