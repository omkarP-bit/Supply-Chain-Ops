from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supplier_id: str
    supplier_code: str
    supplier_name: str
    status: str
    location: str | None = None
    overall_reliability_score: Decimal
    on_time_delivery_rate: Decimal
    quality_score: Decimal
    average_lead_time_days: int
    risk_level: str
    created_at: datetime
    updated_at: datetime


class SupplierMaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supplier_material_id: int
    supplier_id: str
    material_id: str
    available_quantity: Decimal
    reserved_quantity: Decimal
    available_to_promise: Decimal
    unit_price: Decimal
    currency: str
    minimum_order_quantity: Decimal
    maximum_order_quantity: Decimal | None = None
    lead_time_days: int
    expedited_lead_time_days: int | None = None
    aql_level: str | None = None
    material_grade: str | None = None
    certification_valid: bool
    certification_expiry: datetime | None = None
    last_updated: datetime


class EligibleSupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    supplier_id: str
    supplier_name: str
    status: str
    overall_reliability_score: Decimal
    on_time_delivery_rate: Decimal
    quality_score: Decimal
    risk_level: str
    material_id: str
    available_quantity: Decimal
    unit_price: Decimal
    lead_time_days: int
    certification_valid: bool
    score: Decimal
