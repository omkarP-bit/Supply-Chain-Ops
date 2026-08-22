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
REQUIRED_QTY = Decimal("400")
DEADLINE_DAYS = 5


class TestSupplierCandidates:
    def test_get_candidates(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            assert len(candidates) > 0
            supplier_ids = [c.supplier_id for c in candidates]
            assert "SUP-21" in supplier_ids
            assert "SUP-34" in supplier_ids
            assert "SUP-41" in supplier_ids
            assert "SUP-52" in supplier_ids
        _run(_check)

    def test_sup21_rejected(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            sup21 = next(c for c in candidates if c.supplier_id == "SUP-21")
            assert sup21.rejection_reason is not None
            assert sup21.score == Decimal("0")
        _run(_check)

    def test_sup34_eligible(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            sup34 = next(c for c in candidates if c.supplier_id == "SUP-34")
            assert sup34.rejection_reason is None
            assert sup34.score > Decimal("0")
            assert sup34.certification_valid is True
        _run(_check)

    def test_sup41_eligible(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            sup41 = next(c for c in candidates if c.supplier_id == "SUP-41")
            assert sup41.rejection_reason is None
            assert sup41.score > Decimal("0")
            assert sup41.certification_valid is True
        _run(_check)

    def test_sup52_rejected(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            sup52 = next(c for c in candidates if c.supplier_id == "SUP-52")
            assert sup52.rejection_reason is not None
            assert sup52.score == Decimal("0")
        _run(_check)

    def test_sup77_rejected(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            supplier_ids = [c.supplier_id for c in candidates]
            assert "SUP-77" not in supplier_ids
        _run(_check)


class TestSupplierScoring:
    def test_scores_ordering(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            eligible = [c for c in candidates if c.rejection_reason is None]
            assert len(eligible) >= 2
            assert eligible[0].supplier_id == "SUP-34"
        _run(_check)

    def test_supplier_score_weights(self):
        async def _check(session):
            from app.engines.supplier_engine import SupplierEvaluationEngine
            engine = SupplierEvaluationEngine()
            candidates = await engine.get_supplier_candidates(
                session, COMP_104, REQUIRED_QTY, DEADLINE_DAYS
            )
            sup34 = next(c for c in candidates if c.supplier_id == "SUP-34")
            assert sup34.quality_score == Decimal("92")
            assert sup34.reliability_score == Decimal("94")
            assert sup34.on_time_delivery_rate == Decimal("0.9600")
            assert sup34.score > Decimal("80")
        _run(_check)
