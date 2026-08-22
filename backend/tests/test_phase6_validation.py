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


class TestPlanValidation:
    def test_valid_plan(self):
        async def _check(session):
            from app.engines.validation_engine import PlanValidationEngine
            engine = PlanValidationEngine()
            plan = {
                "supplier_id": "SUP-34",
                "material_id": COMP_104,
                "required_quantity": 300,
                "unit_price": 120,
                "deadline_days": 5,
                "total_cost": 36000,
            }
            report = await engine.validate_plan(session, plan)
            assert report.valid is True
            assert len(report.violations) == 0
        _run(_check)

    def test_invalid_quantity(self):
        async def _check(session):
            from app.engines.validation_engine import PlanValidationEngine
            engine = PlanValidationEngine()
            plan = {
                "supplier_id": "SUP-34",
                "material_id": COMP_104,
                "required_quantity": 500,
                "unit_price": 120,
                "deadline_days": 5,
                "total_cost": 60000,
            }
            report = await engine.validate_plan(session, plan)
            assert report.valid is False
            checks = [v["check"] for v in report.violations]
            assert "available_stock" in checks
        _run(_check)

    def test_invalid_lead_time(self):
        async def _check(session):
            from app.engines.validation_engine import PlanValidationEngine
            engine = PlanValidationEngine()
            plan = {
                "supplier_id": "SUP-34",
                "material_id": COMP_104,
                "required_quantity": 300,
                "unit_price": 120,
                "deadline_days": 1,
                "total_cost": 36000,
            }
            report = await engine.validate_plan(session, plan)
            assert report.valid is False
            checks = [v["check"] for v in report.violations]
            assert "delivery_deadline" in checks
        _run(_check)

    def test_invalid_cert(self):
        async def _check(session):
            from app.engines.validation_engine import PlanValidationEngine
            engine = PlanValidationEngine()
            plan = {
                "supplier_id": "SUP-21",
                "material_id": COMP_104,
                "required_quantity": 300,
                "unit_price": 105,
                "deadline_days": 5,
                "total_cost": 31500,
            }
            report = await engine.validate_plan(session, plan)
            assert report.valid is False
            checks = [v["check"] for v in report.violations]
            assert "certification" in checks
        _run(_check)
