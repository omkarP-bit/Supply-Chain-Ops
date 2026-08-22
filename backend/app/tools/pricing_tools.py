from __future__ import annotations

from decimal import Decimal
from typing import Any
from app.engines.pricing_engine import PricingAdjustmentEngine


def calculate_adjusted_pricing(
    original_price: float,
    damage_percentage: float = 0.0,
    quality_degradation: float = 0.0,
) -> dict[str, Any]:
    """Calculate discounted price for damaged/degraded stock deterministically."""
    engine = PricingAdjustmentEngine()
    adj_price = engine.calculate_adjusted_price(
        original_price=Decimal(str(original_price)),
        damage_percentage=Decimal(str(damage_percentage)),
        quality_degradation=Decimal(str(quality_degradation)),
    )
    return {
        "original_price": original_price,
        "damage_percentage": damage_percentage,
        "quality_degradation": quality_degradation,
        "effective_price": float(adj_price),
        "discount_applied": float(Decimal(str(original_price)) - adj_price),
    }
