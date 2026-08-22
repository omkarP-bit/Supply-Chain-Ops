import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import incident_repo
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentBrief
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/api/v1", tags=["incidents"])


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: AsyncSession = Depends(get_db),
):
    incident = await incident_repo.create_incident(
        db,
        incident_id=uuid.uuid4().hex[:16],
        **payload.model_dump(),
    )
    return incident


@router.get("/incidents", response_model=PaginatedResponse)
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    incidents = await incident_repo.list_incidents(db, skip=skip, limit=limit, status=status)
    items = [
        {
            "incident_id": i.incident_id,
            "incident_type": i.incident_type,
            "material_id": i.material_id,
            "po_id": i.po_id,
            "supplier_id": i.supplier_id,
            "description": i.description,
            "severity": i.severity,
            "status": i.status,
            "workflow_state": i.workflow_state,
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "updated_at": i.updated_at.isoformat() if i.updated_at else None,
            "recovery_plans": [],
            "approval_requests": [],
        }
        for i in incidents
    ]
    return PaginatedResponse(
        items=items,
        total=len(items),
        skip=skip,
        limit=limit,
    )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
):
    incident = await incident_repo.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
