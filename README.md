# Autonomous Supply Chain Recovery System

AI-assisted supply-chain disruption management platform.

> **LLMs recommend and reason. Deterministic services establish operational truth.
> Humans authorize. Deterministic tools execute.**

## Stack

- Frontend: React (Vite)
- Backend: FastAPI (Python 3.13)
- Database: PostgreSQL 16 (Docker), SQLAlchemy 2.x async + asyncpg, Alembic
- Agents: Supervisor / Recovery & Recommendation / Verification & Replanning (LLM provider configurable; deterministic mock fallback)
- Testing: Pytest

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000 (`GET /health`)
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5433

## Local development

```bash
docker run -d --name scops-postgres -e POSTGRES_USER=scops -e POSTGRES_PASSWORD=scops_secret \
  -e POSTGRES_DB=supply_chain -p 5433:5432 postgres:16

cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
cd backend && pytest -v
```

Phase-by-phase test logs are stored in `TEST_LOGS.md` at the repository root.

## Layout

See `PROJECT.md` for architecture and `DEVELOPMENT_PHASES.md` for the build plan.
