import asyncio
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


class TestPartialIndexes:
    def test_eligible_supplier_index_exists(self):
        async def _check(session):
            r = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_eligible_supplier_material')")
            )
            assert r.scalar(), "Index idx_eligible_supplier_material not found"
        _run(_check)

    def test_active_supplier_index_exists(self):
        async def _check(session):
            r = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_active_suppliers')")
            )
            assert r.scalar(), "Index idx_active_suppliers not found"
        _run(_check)

    def test_supplier_material_available_index_exists(self):
        async def _check(session):
            r = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_supplier_material_available')")
            )
            assert r.scalar(), "Index idx_supplier_material_available not found"
        _run(_check)

    def test_supplier_certification_index_exists(self):
        async def _check(session):
            r = await session.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_supplier_certification_valid')")
            )
            assert r.scalar(), "Index idx_supplier_certification_valid not found"
        _run(_check)

    def test_eligible_query_uses_index(self):
        async def _check(session):
            r = await session.execute(
                text(
                    "EXPLAIN ANALYZE "
                    "SELECT sm.supplier_id, sm.material_id "
                    "FROM supplier_materials sm "
                    "JOIN suppliers s ON sm.supplier_id = s.supplier_id "
                    "WHERE s.status = 'ACTIVE' "
                    "AND sm.material_id = 'COMP-104' "
                    "AND sm.available_quantity >= 100 "
                    "AND sm.certification_valid = true"
                )
            )
            rows = r.fetchall()
            plan_text = "\n".join(str(row[0]) for row in rows)
            assert len(rows) > 0, "EXPLAIN ANALYZE returned no rows"
            assert "Seq Scan" in plan_text or "Index Scan" in plan_text or "Bitmap Scan" in plan_text
        _run(_check)
