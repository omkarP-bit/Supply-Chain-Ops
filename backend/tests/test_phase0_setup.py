import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "up"


def test_openapi_available():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/health" in paths


def test_database_url_configured():
    from app.config import settings

    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert ":5433/" in settings.database_url or ":5432/" in settings.database_url


def test_httpx_async_health():
    import asyncio

    from app.config import settings

    async def _hit():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.get("/health")

    resp = asyncio.run(_hit())
    assert resp.status_code == 200
    assert resp.json()["database"] in ("up", "down")
