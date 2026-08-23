from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db.session import get_db
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/api/v1", tags=["scenarios"])
scenario_service = ScenarioService()


@router.get("/scenarios")
async def list_scenarios(db: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    """List the 6 official hackathon scenarios with their live execution statuses."""
    return await scenario_service.list_scenarios(db)


@router.post("/scenarios/{scenario_id}/inject")
async def inject_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Inject real persisted disruption data, trigger LangGraph workflow, and generate real incident dossier."""
    try:
        return await scenario_service.inject_scenario(db, scenario_id.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario execution failed: {str(e)}")


@router.post("/scenarios/{scenario_id}/reset")
async def reset_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Reset simulation baseline data safely for repeatable testing."""
    try:
        return await scenario_service.reset_scenario(db, scenario_id.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario reset failed: {str(e)}")
