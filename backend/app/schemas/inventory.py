from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InventorySnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_id: int
    material_id: str
    warehouse_id: str
    snapshot_date: datetime
    erp_quantity: Decimal
    physical_quantity: Decimal
    usable_quantity: Decimal
    reserved_quantity: Decimal
    damaged_quantity: Decimal
    blocked_quantity: Decimal
    in_transit_quantity: Decimal
    available_quantity: Decimal
    source: str
    created_at: datetime


class InventoryCoverageResponse(BaseModel):
    material_id: str
    usable_stock: Decimal
    avg_daily_consumption_30d: Decimal
    avg_daily_consumption_7d: Decimal
    coverage_days: Decimal
    trend_7d_vs_30d: str


class InventoryDiscrepancyResponse(BaseModel):
    material_id: str
    erp_quantity: Decimal
    physical_quantity: Decimal
    discrepancy_percentage: Decimal
    is_stale: bool


class InventoryHistoryResponse(BaseModel):
    snapshots: list[InventorySnapshotResponse]
