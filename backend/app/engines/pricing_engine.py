from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory import InventorySnapshot
from app.db.models.materials import MaterialSpecification


class PricingAdjustmentEngine:

    async def validate_damaged_stock(
        self, session: AsyncSession, material_id: str, damage_percentage: Decimal
    ) -> tuple[bool, str]:
        if damage_percentage < Decimal("0") or damage_percentage > Decimal("100"):
            return False, f"Damage percentage must be between 0 and 100, got {damage_percentage}"

        stmt = (
            select(InventorySnapshot)
            .where(InventorySnapshot.material_id == material_id)
            .order_by(InventorySnapshot.snapshot_date.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        if not snapshot:
            return False, "No inventory snapshot found"

        damaged_qty = snapshot.damaged_quantity or Decimal("0")
        total_qty = snapshot.physical_quantity or Decimal("0")
        if total_qty > Decimal("0"):
            actual_damage_pct = (damaged_qty / total_qty) * Decimal("100")
            if damage_percentage > actual_damage_pct * Decimal("1.2"):
                return False, (
                    f"Claimed damage {damage_percentage}% exceeds "
                    f"recorded damage {actual_damage_pct.quantize(Decimal('0.01'))}%"
                )

        spec_stmt = select(MaterialSpecification).where(
            MaterialSpecification.material_id == material_id
        )
        spec_result = await session.execute(spec_stmt)
        spec = spec_result.scalar_one_or_none()

        if spec and spec.required_certifications:
            if damage_percentage > Decimal("50"):
                return False, "Damage too high for materials requiring certification; reject stock"

        return True, "Damage validation passed"

    def calculate_adjusted_price(
        self,
        original_price: Decimal,
        damage_percentage: Decimal,
        quality_degradation: Decimal = Decimal("0"),
    ) -> Decimal:
        if damage_percentage < Decimal("0") or damage_percentage > Decimal("100"):
            raise ValueError("Damage percentage must be between 0 and 100")

        damage_factor = Decimal("1") - (damage_percentage / Decimal("100"))
        adjusted = original_price * damage_factor

        if quality_degradation > Decimal("0"):
            quality_factor = Decimal("1") - (quality_degradation / Decimal("100"))
            adjusted = adjusted * quality_factor

        return adjusted.quantize(Decimal("0.01"))
