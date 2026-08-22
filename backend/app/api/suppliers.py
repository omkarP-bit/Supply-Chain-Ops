import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories import supplier_repo
from app.engines.supplier_engine import SupplierEvaluationEngine
from app.schemas.supplier import SupplierResponse, EligibleSupplierResponse

router = APIRouter(prefix="/api/v1", tags=["suppliers"])

supplier_engine = SupplierEvaluationEngine()


@router.get("/suppliers", response_model=list[SupplierResponse])
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    return await supplier_repo.list_active_suppliers(db)


@router.get("/suppliers/eligible/{material_id}", response_model=list[EligibleSupplierResponse])
async def get_eligible_suppliers(
    material_id: str,
    required_quantity: Decimal = Query(..., gt=0),
    deadline_days: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    candidates = await supplier_engine.get_supplier_candidates(
        db, material_id, required_quantity, deadline_days
    )

    result = []
    for c in candidates:
        if c.rejection_reason:
            continue
        result.append(
            EligibleSupplierResponse(
                supplier_id=str(c.supplier_id),
                supplier_name=c.supplier_name,
                status="ACTIVE",
                overall_reliability_score=c.reliability_score,
                on_time_delivery_rate=c.on_time_delivery_rate,
                quality_score=c.quality_score,
                risk_level="LOW" if c.score > 60 else "MEDIUM" if c.score > 40 else "HIGH",
                material_id=material_id,
                available_quantity=c.available_quantity,
                unit_price=c.unit_price,
                lead_time_days=c.lead_time_days,
                certification_valid=c.certification_valid,
                score=c.score,
            )
        )

    return result


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
):
    supplier = await supplier_repo.get_supplier(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier
