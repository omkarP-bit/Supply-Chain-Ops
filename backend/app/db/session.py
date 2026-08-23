from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=300,
        )
    return _engine


def reset_engine():
    global _engine, _session_factory
    if _engine is not None:
        _engine = None
    if _session_factory is not None:
        _session_factory = None


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def get_db():
    async with get_session_factory()() as session:
        yield session


def _lazy_engine_proxy():
    class _Proxy:
        def __getattr__(self, name):
            return getattr(get_engine(), name)
    return _Proxy()


engine = _lazy_engine_proxy()
AsyncSessionLocal = get_session_factory
