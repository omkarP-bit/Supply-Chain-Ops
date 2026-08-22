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


class TestSimulation:
    def test_simulate_plan(self):
        async def _check(session):
            from app.engines.simulation_engine import SimulationEngine
            engine = SimulationEngine()
            plan = {
                "material_id": COMP_104,
                "supplier_id": "SUP-34",
                "required_quantity": 500,
                "unit_price": 120,
                "deadline_days": 2,
                "plan_id": "SIM-TEST-001",
            }
            result = await engine.simulate_plan(session, plan)
            assert result.plan_id == "SIM-TEST-001"
            assert result.total_cost == Decimal("60000")
            assert result.inventory_after_recovery == Decimal("890")
            assert result.delivery_date is not None
            assert result.production_impact_hours >= 0.0
        _run(_check)

    def test_simulation_feasibility(self):
        async def _check(session):
            from app.engines.simulation_engine import SimulationEngine
            engine = SimulationEngine()
            plan = {
                "material_id": COMP_104,
                "supplier_id": "SUP-34",
                "required_quantity": 500,
                "unit_price": 120,
                "deadline_days": 2,
            }
            result = await engine.simulate_plan(session, plan)
            assert result.feasible is True
            assert result.production_coverage_days > Decimal("1")
        _run(_check)

    def test_simulation_with_partial(self):
        async def _check(session):
            from app.engines.simulation_engine import SimulationEngine
            engine = SimulationEngine()
            plan = {
                "material_id": COMP_104,
                "supplier_id": "SUP-34",
                "required_quantity": 200,
                "unit_price": 120,
                "deadline_days": 2,
                "plan_id": "SIM-PARTIAL-001",
            }
            result = await engine.simulate_plan(session, plan)
            assert result.plan_id == "SIM-PARTIAL-001"
            assert result.total_cost == Decimal("24000")
            assert result.inventory_after_recovery == Decimal("590")
            assert result.feasible is True
        _run(_check)
