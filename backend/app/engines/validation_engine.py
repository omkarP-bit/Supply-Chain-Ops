from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory import InventorySnapshot
from app.db.models.suppliers import Supplier, SupplierMaterial
from app.db.models.materials import MaterialSpecification
from app.db.models.risk import RiskThreshold


@dataclass
class ValidationReport:
    valid: bool = True
    violations: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)


class PlanValidationEngine:

    async def validate_plan(
        self, session: AsyncSession, plan_dict: dict[str, Any]
    ) -> ValidationReport:
        report = ValidationReport()

        supplier_id = plan_dict.get("supplier_id")
        material_id = plan_dict.get("material_id")
        required_quantity = Decimal(str(plan_dict.get("required_quantity", 0)))
        unit_price = Decimal(str(plan_dict.get("unit_price", 0)))
        deadline_days = plan_dict.get("deadline_days")
        total_cost = Decimal(str(plan_dict.get("total_cost", 0)))

        await self._check_supplier_active(session, supplier_id, report)
        await self._check_available_stock(session, material_id, required_quantity, report)
        await self._check_delivery_deadline(deadline_days, session, supplier_id, material_id, report)
        await self._check_certification(session, supplier_id, material_id, report)
        await self._check_aql(session, supplier_id, material_id, report)
        await self._check_budget(total_cost, required_quantity, unit_price, report)
        await self._check_moq(session, supplier_id, material_id, required_quantity, report)

        report.valid = len(report.violations) == 0
        return report

    async def _check_supplier_active(
        self, session: AsyncSession, supplier_id: str, report: ValidationReport
    ):
        if not supplier_id:
            report.violations.append({"check": "supplier_active", "message": "No supplier specified"})
            return
        stmt = select(Supplier).where(Supplier.supplier_id == supplier_id)
        result = await session.execute(stmt)
        supplier = result.scalar_one_or_none()
        if not supplier:
            report.violations.append({"check": "supplier_active", "message": "Supplier not found"})
            return
        if supplier.status != "ACTIVE":
            report.violations.append({
                "check": "supplier_active",
                "message": f"Supplier status is {supplier.status}, not ACTIVE",
            })

    async def _check_available_stock(
        self,
        session: AsyncSession,
        material_id: str,
        required_quantity: Decimal,
        report: ValidationReport,
    ):
        if not material_id:
            report.violations.append({"check": "available_stock", "message": "No material specified"})
            return
        stmt = (
            select(InventorySnapshot)
            .where(InventorySnapshot.material_id == material_id)
            .order_by(InventorySnapshot.snapshot_date.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            report.warnings.append({"check": "available_stock", "message": "No inventory snapshot found"})
            return
        available = snapshot.usable_quantity or Decimal("0")
        if available < required_quantity:
            report.violations.append({
                "check": "available_stock",
                "message": f"Available {available} < required {required_quantity}",
            })

    async def _check_delivery_deadline(
        self,
        deadline_days: int | None,
        session: AsyncSession,
        supplier_id: str,
        material_id: str,
        report: ValidationReport,
    ):
        if deadline_days is None:
            return
        if not supplier_id or not material_id:
            return
        stmt = select(SupplierMaterial).where(
            and_(
                SupplierMaterial.supplier_id == supplier_id,
                SupplierMaterial.material_id == material_id,
            )
        )
        result = await session.execute(stmt)
        sm = result.scalar_one_or_none()
        if not sm:
            return
        lead = sm.lead_time_days or 0
        if lead > deadline_days:
            report.violations.append({
                "check": "delivery_deadline",
                "message": f"Lead time {lead}d exceeds deadline {deadline_days}d",
            })

    async def _check_certification(
        self,
        session: AsyncSession,
        supplier_id: str,
        material_id: str,
        report: ValidationReport,
    ):
        if not supplier_id or not material_id:
            return
        spec_stmt = select(MaterialSpecification).where(
            MaterialSpecification.material_id == material_id
        )
        spec_result = await session.execute(spec_stmt)
        spec = spec_result.scalar_one_or_none()
        if not spec or not spec.required_certifications:
            return

        sm_stmt = select(SupplierMaterial).where(
            and_(
                SupplierMaterial.supplier_id == supplier_id,
                SupplierMaterial.material_id == material_id,
            )
        )
        sm_result = await session.execute(sm_stmt)
        sm = sm_result.scalar_one_or_none()
        if not sm:
            report.violations.append({
                "check": "certification",
                "message": "Supplier-material link not found",
            })
            return
        if not sm.certification_valid:
            report.violations.append({
                "check": "certification",
                "message": "Supplier certification is invalid or expired",
            })

    async def _check_aql(
        self,
        session: AsyncSession,
        supplier_id: str,
        material_id: str,
        report: ValidationReport,
    ):
        if not supplier_id or not material_id:
            return
        spec_stmt = select(MaterialSpecification).where(
            MaterialSpecification.material_id == material_id
        )
        spec_result = await session.execute(spec_stmt)
        spec = spec_result.scalar_one_or_none()
        if not spec or not spec.aql_level:
            return

        sm_stmt = select(SupplierMaterial).where(
            and_(
                SupplierMaterial.supplier_id == supplier_id,
                SupplierMaterial.material_id == material_id,
            )
        )
        sm_result = await session.execute(sm_stmt)
        sm = sm_result.scalar_one_or_none()
        if not sm or not sm.aql_level:
            report.warnings.append({
                "check": "aql",
                "message": "AQL level not specified for supplier material",
            })
            return
        if sm.aql_level != spec.aql_level:
            report.violations.append({
                "check": "aql",
                "message": f"AQL mismatch: supplier={sm.aql_level}, required={spec.aql_level}",
            })

    async def _check_budget(
        self,
        total_cost: Decimal,
        required_quantity: Decimal,
        unit_price: Decimal,
        report: ValidationReport,
    ):
        if total_cost <= Decimal("0"):
            report.warnings.append({"check": "budget", "message": "Total cost is zero or not set"})
            return
        expected = required_quantity * unit_price
        if expected > Decimal("0") and total_cost > expected * Decimal("1.1"):
            report.violations.append({
                "check": "budget",
                "message": f"Total cost {total_cost} significantly exceeds expected {expected}",
            })

    async def _check_moq(
        self,
        session: AsyncSession,
        supplier_id: str,
        material_id: str,
        required_quantity: Decimal,
        report: ValidationReport,
    ):
        if not supplier_id or not material_id:
            return
        stmt = select(SupplierMaterial).where(
            and_(
                SupplierMaterial.supplier_id == supplier_id,
                SupplierMaterial.material_id == material_id,
            )
        )
        result = await session.execute(stmt)
        sm = result.scalar_one_or_none()
        if not sm:
            return
        moq = sm.minimum_order_quantity or Decimal("0")
        if required_quantity < moq:
            report.violations.append({
                "check": "moq",
                "message": f"Quantity {required_quantity} below MOQ {moq}",
            })
