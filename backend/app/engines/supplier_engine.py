from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.suppliers import Supplier, SupplierMaterial, SupplierPerformance
from app.db.models.materials import Material, MaterialSpecification


@dataclass
class SupplierCandidate:
    supplier_id: str
    supplier_name: str
    available_quantity: Decimal
    unit_price: Decimal
    currency: str
    lead_time_days: int
    certification_valid: bool
    aql_level: str
    material_grade: str
    quality_score: Decimal
    reliability_score: Decimal
    on_time_delivery_rate: Decimal
    score: Decimal
    rejection_reason: Optional[str] = None


class SupplierEvaluationEngine:

    async def get_supplier_candidates(
        self,
        session: AsyncSession,
        material_id: str,
        required_quantity: Decimal,
        deadline_days: Optional[int] = None,
    ) -> list[SupplierCandidate]:
        stmt = (
            select(SupplierMaterial, Supplier)
            .join(Supplier, SupplierMaterial.supplier_id == Supplier.supplier_id)
            .where(
                and_(
                    SupplierMaterial.material_id == material_id,
                    Supplier.status == "ACTIVE",
                )
            )
        )
        result = await session.execute(stmt)
        rows = result.all()

        candidates: list[SupplierCandidate] = []

        for sm, supplier in rows:
            passed, reason = self._run_hard_filters(
                sm, supplier, required_quantity, deadline_days
            )
            if not passed:
                candidates.append(
                    SupplierCandidate(
                        supplier_id=supplier.supplier_id,
                        supplier_name=supplier.supplier_name,
                        available_quantity=sm.available_quantity or Decimal("0"),
                        unit_price=sm.unit_price or Decimal("0"),
                        currency=sm.currency or "INR",
                        lead_time_days=sm.lead_time_days or 0,
                        certification_valid=sm.certification_valid or False,
                        aql_level=sm.aql_level or "",
                        material_grade=sm.material_grade or "",
                        quality_score=supplier.quality_score or Decimal("0"),
                        reliability_score=supplier.overall_reliability_score or Decimal("0"),
                        on_time_delivery_rate=supplier.on_time_delivery_rate or Decimal("0"),
                        score=Decimal("0"),
                        rejection_reason=reason,
                    )
                )
                continue

            score = await self.calculate_supplier_score(session, sm)

            candidates.append(
                SupplierCandidate(
                    supplier_id=supplier.supplier_id,
                    supplier_name=supplier.supplier_name,
                    available_quantity=sm.available_quantity or Decimal("0"),
                    unit_price=sm.unit_price or Decimal("0"),
                    currency=sm.currency or "INR",
                    lead_time_days=sm.lead_time_days or 0,
                    certification_valid=sm.certification_valid or False,
                    aql_level=sm.aql_level or "",
                    material_grade=sm.material_grade or "",
                    quality_score=supplier.quality_score or Decimal("0"),
                    reliability_score=supplier.overall_reliability_score or Decimal("0"),
                    on_time_delivery_rate=supplier.on_time_delivery_rate or Decimal("0"),
                    score=score,
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    def _run_hard_filters(
        self,
        sm: SupplierMaterial,
        supplier: Supplier,
        required_quantity: Decimal,
        deadline_days: Optional[int],
    ) -> tuple[bool, str]:
        passed, reason = self.check_stock(sm, required_quantity)
        if not passed:
            return False, reason

        passed, reason = self.check_certification(sm)
        if not passed:
            return False, reason

        passed, reason = self.check_lead_time(sm, deadline_days)
        if not passed:
            return False, reason

        passed, reason = self.check_moq(sm, required_quantity)
        if not passed:
            return False, reason

        return True, ""

    def check_stock(
        self, sm: SupplierMaterial, required_quantity: Decimal
    ) -> tuple[bool, str]:
        available = sm.available_to_promise or sm.available_quantity or Decimal("0")
        if available >= required_quantity:
            return True, "OK"
        return False, f"Insufficient stock: {available} < {required_quantity}"

    def check_certification(self, sm: SupplierMaterial) -> tuple[bool, str]:
        if sm.certification_valid:
            return True, "OK"
        return False, "Certification expired or invalid"

    def check_aql(self, sm: SupplierMaterial) -> tuple[bool, str]:
        if not sm.aql_level:
            return True, "OK"
        valid_levels = {"I", "II", "III", "S-1", "S-2", "S-3", "S-4"}
        if sm.aql_level.upper() in valid_levels:
            return True, "OK"
        return False, f"Invalid AQL level: {sm.aql_level}"

    def check_material_grade(self, sm: SupplierMaterial) -> tuple[bool, str]:
        if sm.material_grade and sm.material_grade.strip():
            return True, "OK"
        return False, "Material grade not specified"

    def check_specification_match(
        self,
        session: AsyncSession,
        sm: SupplierMaterial,
        material_id: str,
    ) -> tuple[bool, str]:
        stmt = select(MaterialSpecification).where(
            MaterialSpecification.material_id == material_id
        )
        result = session.execute(stmt)
        spec = result.scalar_one_or_none()
        if not spec:
            return True, "No specification found"
        if sm.material_grade and sm.material_grade == spec.material_grade:
            return True, "Specification matches"
        return False, f"Grade mismatch: supplier={sm.material_grade}, required={spec.material_grade}"

    def check_lead_time(
        self, sm: SupplierMaterial, deadline_days: Optional[int]
    ) -> tuple[bool, str]:
        lead = sm.lead_time_days or 0
        if deadline_days is None:
            return True, "OK"
        if lead <= deadline_days:
            return True, "OK"
        return False, f"Lead time {lead}d exceeds deadline {deadline_days}d"

    def check_moq(self, sm: SupplierMaterial, required_quantity: Decimal) -> tuple[bool, str]:
        moq = sm.minimum_order_quantity or Decimal("0")
        max_qty = sm.maximum_order_quantity
        if required_quantity < moq:
            return False, f"Below MOQ: {required_quantity} < {moq}"
        if max_qty and required_quantity > max_qty:
            return False, f"Above max order: {required_quantity} > {max_qty}"
        return True, "OK"

    async def calculate_supplier_score(
        self, session: AsyncSession, sm: SupplierMaterial
    ) -> Decimal:
        stmt = select(Supplier).where(Supplier.supplier_id == sm.supplier_id)
        result = await session.execute(stmt)
        supplier = result.scalar_one_or_none()
        if not supplier:
            return Decimal("0")

        quality = (supplier.quality_score or Decimal("0")) / Decimal("100") * Decimal("30")

        reliability = (supplier.overall_reliability_score or Decimal("0")) / Decimal("100") * Decimal("25")

        available = sm.available_to_promise or sm.available_quantity or Decimal("0")
        availability_score = min(available / Decimal("1000"), Decimal("1")) * Decimal("20")

        price = sm.unit_price or Decimal("0")
        if price > Decimal("0"):
            price_score = (Decimal("1") / (price / Decimal("100"))) * Decimal("15")
            price_score = min(price_score, Decimal("15"))
        else:
            price_score = Decimal("15")

        lead = sm.lead_time_days or 30
        lead_score = (Decimal("1") - Decimal(str(min(lead, 30))) / Decimal("30")) * Decimal("10")

        total = quality + reliability + availability_score + price_score + lead_score
        return total.quantize(Decimal("0.01"))
