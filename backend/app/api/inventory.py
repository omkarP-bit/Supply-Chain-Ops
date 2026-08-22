import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import inventory_repo
from app.engines.risk_engine import OperationalRiskEngine
from app.schemas.inventory import (
    InventorySnapshotResponse,
    InventoryCoverageResponse,
    InventoryHistoryResponse,
)

router = APIRouter(prefix="/api/v1", tags=["inventory"])

risk_engine = OperationalRiskEngine()


@router.get("/inventory/{material_id}", response_model=InventorySnapshotResponse)
async def get_latest_snapshot(
    material_id: str,
    db: AsyncSession = Depends(get_db),
):
    snapshot = await inventory_repo.get_latest_snapshot(db, material_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No inventory snapshot found")
    return snapshot


@router.get("/inventory/{material_id}/coverage", response_model=InventoryCoverageResponse)
async def get_coverage_analysis(
    material_id: str,
    db: AsyncSession = Depends(get_db),
):
    coverage = await risk_engine.calculate_inventory_coverage(db, material_id)
    discrepancy = await risk_engine.calculate_inventory_discrepancy(db, material_id)
    snapshot = await risk_engine.get_current_inventory(db, material_id)

    if not snapshot:
        raise HTTPException(status_code=404, detail="No inventory data found")

    return InventoryCoverageResponse(
        material_id=material_id,
        usable_stock=snapshot.usable_quantity or Decimal("0"),
        avg_daily_consumption_30d=await risk_engine.calculate_average_consumption_30d(db, material_id),
        avg_daily_consumption_7d=await risk_engine.calculate_average_consumption_7d(db, material_id),
        coverage_days=coverage["coverage_days"],
        trend_7d_vs_30d=coverage["trend"],
    )


@router.get("/inventory/{material_id}/history", response_model=InventoryHistoryResponse)
async def get_inventory_history(
    material_id: str,
    days: int = Query(35, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    snapshots = await inventory_repo.get_snapshot_history(db, material_id, days=days)
    return InventoryHistoryResponse(snapshots=snapshots)
