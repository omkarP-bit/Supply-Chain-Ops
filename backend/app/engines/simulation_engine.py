from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory import InventorySnapshot
from app.engines.risk_engine import OperationalRiskEngine


@dataclass
class SimulationResult:
    plan_id: str
    inventory_after_recovery: Decimal
    production_coverage_days: Decimal
    delivery_date: datetime
    production_stop_avoided: bool
    total_cost: Decimal
    remaining_risk_level: str
    production_impact_hours: float
    feasible: bool


class SimulationEngine:

    def __init__(self):
        self.risk_engine = OperationalRiskEngine()

    async def simulate_plan(
        self, session: AsyncSession, plan_dict: dict[str, Any]
    ) -> SimulationResult:
        material_id = plan_dict["material_id"]
        supplier_id = plan_dict["supplier_id"]
        required_quantity = Decimal(str(plan_dict.get("required_quantity", 0)))
        unit_price = Decimal(str(plan_dict.get("unit_price", 0)))
        deadline_days = int(plan_dict.get("deadline_days", 0))
        plan_id = plan_dict.get("plan_id", str(uuid.uuid4()))

        snapshot = await self.risk_engine.get_current_inventory(session, material_id)
        current_usable = (snapshot.usable_quantity or Decimal("0")) if snapshot else Decimal("0")
        current_coverage = await self.risk_engine.calculate_inventory_coverage(session, material_id)
        current_coverage_days = current_coverage["coverage_days"]

        avg_consumption = await self.risk_engine.calculate_average_consumption_30d(session, material_id)

        inventory_after_recovery = current_usable + required_quantity

        if avg_consumption > Decimal("0"):
            production_coverage_days = inventory_after_recovery / avg_consumption
        else:
            production_coverage_days = Decimal("999") if inventory_after_recovery > Decimal("0") else Decimal("0")

        delivery_date = datetime.utcnow() + timedelta(days=deadline_days)

        current_hours_stop = await self.risk_engine.calculate_hours_to_production_stop(session, material_id)
        production_stop_avoided = current_hours_stop < float("inf") and (
            current_hours_stop < deadline_days * 24
        )

        total_cost = required_quantity * unit_price

        if production_coverage_days < Decimal("3"):
            remaining_risk_level = "CRITICAL"
        elif production_coverage_days < Decimal("7"):
            remaining_risk_level = "HIGH"
        elif production_coverage_days < Decimal("14"):
            remaining_risk_level = "MEDIUM"
        elif production_coverage_days < Decimal("21"):
            remaining_risk_level = "LOW"
        else:
            remaining_risk_level = "NONE"

        production_impact_hours = max(0.0, (deadline_days * 24) - current_hours_stop) if current_hours_stop < float("inf") else 0.0

        feasible = (
            inventory_after_recovery > Decimal("0")
            and production_coverage_days >= Decimal("1")
            and total_cost > Decimal("0")
        )

        return SimulationResult(
            plan_id=plan_id,
            inventory_after_recovery=inventory_after_recovery,
            production_coverage_days=production_coverage_days.quantize(Decimal("0.1")),
            delivery_date=delivery_date,
            production_stop_avoided=production_stop_avoided,
            total_cost=total_cost,
            remaining_risk_level=remaining_risk_level,
            production_impact_hours=production_impact_hours,
            feasible=feasible,
        )
