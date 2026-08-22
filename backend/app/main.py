from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.session import engine, get_session_factory
from app.db.models.base import Base
import app.db.models.materials
import app.db.models.suppliers
import app.db.models.inventory
import app.db.models.production
import app.db.models.procurement
import app.db.models.risk
import app.db.models.workflow
import app.db.models.contract_models
from app.db.seed import seed_db
from app.seed.seed_data import seed_contract_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    async with factory() as session:
        await seed_db(session)
        await seed_contract_data(session)
    yield


app = FastAPI(title=settings.project_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import incidents, inventory, dashboard, approvals, suppliers, recovery, audit, contract_api

# Existing routers
app.include_router(incidents.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)
app.include_router(approvals.router)
app.include_router(suppliers.router)
app.include_router(recovery.router)
app.include_router(audit.router)

# Contract API routers (available both at root / and /api/v1)
app.include_router(contract_api.router)
app.include_router(contract_api.router, prefix="/api/v1")


@app.get("/health")
async def health():
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "up" if db_ok else "down"}
