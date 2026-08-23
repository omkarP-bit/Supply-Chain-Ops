from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inventory import InventorySnapshot, InventoryMovement
from app.db.models.production import ProductionOrder, ProductionConsumption
from app.db.models.materials import Material
from app.db.models.risk import RiskThreshold


@dataclass
class RiskReport:
    material_id: str
    risk_level: str
    usable_stock: Decimal
    avg_daily_consumption_30d: Decimal
    avg_daily_consumption_7d: Decimal
    coverage_days: Decimal
    inventory_discrepancy: Decimal
    discrepancy_percentage: Decimal
    erp_quantity: Decimal
    physical_quantity: Decimal
    affected_orders: list = field(default_factory=list)
    hours_to_production_stop: float = 0.0
    threshold_violations: list = field(default_factory=list)
    trend_7d_vs_30d: str = ""


class OperationalRiskEngine:
    async def get_current_inventory(
        self, session: AsyncSession, material_id: str
    ) -> Optional[InventorySnapshot]:
        stmt = (
            select(InventorySnapshot)
            .where(InventorySnapshot.material_id == material_id)
            .order_by(InventorySnapshot.snapshot_date.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        snap = result.scalar_one_or_none()
        if snap:
            return snap

        # Fallback to Component record
        try:
            from app.db.models.contract_models import Component
            comp = (await session.execute(select(Component).where(Component.component_id == material_id))).scalar_one_or_none()
            if comp:
                usable = Decimal(str(comp.usable_stock if comp.usable_stock is not None else 500))
                return InventorySnapshot(
                    snapshot_id=f"snap-{material_id}",
                    material_id=material_id,
                    plant_id="PLANT-PUNE",
                    snapshot_date=datetime.now(timezone.utc),
                    erp_quantity=usable * Decimal("1.05"),
                    physical_count_quantity=usable,
                    usable_quantity=usable,
                    quarantine_quantity=Decimal("0"),
                    allocated_quantity=Decimal("0"),
                )
        except Exception:
            pass
        return None

    async def get_inventory_history(
        self, session: AsyncSession, material_id: str, days: int = 35
    ) -> list[InventorySnapshot]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(InventorySnapshot)
            .where(
                and_(
                    InventorySnapshot.material_id == material_id,
                    InventorySnapshot.snapshot_date >= cutoff,
                )
            )
            .order_by(InventorySnapshot.snapshot_date.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def calculate_average_consumption_30d(
        self, session: AsyncSession, material_id: str
    ) -> Decimal:
        history = await self.get_inventory_history(session, material_id, days=35)
        if len(history) < 2:
            try:
                from app.db.models.contract_models import Component
                comp = (await session.execute(select(Component).where(Component.component_id == material_id))).scalar_one_or_none()
                if comp and comp.daily_usage:
                    return Decimal(str(comp.daily_usage))
            except Exception:
                pass
            return Decimal("25.0")

        daily_deltas: list[Decimal] = []
        for i in range(len(history) - 1):
            current = history[i]
            previous = history[i + 1]
            days_diff = (current.snapshot_date - previous.snapshot_date).days
            if days_diff <= 0:
                continue
            available_now = current.usable_quantity or Decimal("0")
            available_prev = previous.usable_quantity or Decimal("0")
            delta = available_prev - available_now
            if delta > Decimal("0"):
                daily_deltas.append(delta / Decimal(str(days_diff)))

        if not daily_deltas:
            try:
                from app.db.models.contract_models import Component
                comp = (await session.execute(select(Component).where(Component.component_id == material_id))).scalar_one_or_none()
                if comp and comp.daily_usage:
                    return Decimal(str(comp.daily_usage))
            except Exception:
                pass
            return Decimal("25.0")

        return sum(daily_deltas) / Decimal(str(len(daily_deltas)))

    async def calculate_average_consumption_7d(
        self, session: AsyncSession, material_id: str
    ) -> Decimal:
        history = await self.get_inventory_history(session, material_id, days=14)
        recent = [h for h in history if h.snapshot_date >= datetime.now(timezone.utc) - timedelta(days=7)]
        if len(recent) < 2:
            return await self.calculate_average_consumption_30d(session, material_id)

        daily_deltas: list[Decimal] = []
        for i in range(len(recent) - 1):
            current = recent[i]
            previous = recent[i + 1]
            days_diff = (current.snapshot_date - previous.snapshot_date).days
            if days_diff <= 0:
                continue
            available_now = current.usable_quantity or Decimal("0")
            available_prev = previous.usable_quantity or Decimal("0")
            delta = available_prev - available_now
            if delta > Decimal("0"):
                daily_deltas.append(delta / Decimal(str(days_diff)))

        if not daily_deltas:
            return await self.calculate_average_consumption_30d(session, material_id)

        return sum(daily_deltas) / Decimal(str(len(daily_deltas)))

    async def calculate_inventory_coverage(
        self, session: AsyncSession, material_id: str
    ) -> dict:
        snapshot = await self.get_current_inventory(session, material_id)
        if not snapshot:
            return {"coverage_days": Decimal("14.0"), "trend": "STABLE"}

        usable = snapshot.usable_quantity or Decimal("0")
        avg_30d = await self.calculate_average_consumption_30d(session, material_id)
        avg_7d = await self.calculate_average_consumption_7d(session, material_id)

        if avg_30d <= Decimal("0"):
            coverage = Decimal("999") if usable > Decimal("0") else Decimal("0")
        else:
            coverage = usable / avg_30d

        trend = "STABLE"
        if avg_7d > avg_30d * Decimal("1.1"):
            trend = "INCREASING"
        elif avg_7d < avg_30d * Decimal("0.9"):
            trend = "DECREASING"

        return {"coverage_days": coverage.quantize(Decimal("0.1")), "trend": trend}

    async def calculate_inventory_discrepancy(
        self, session: AsyncSession, material_id: str
    ) -> dict:
        snapshot = await self.get_current_inventory(session, material_id)
        if not snapshot:
            return {"discrepancy": Decimal("0"), "discrepancy_percentage": Decimal("0")}

        erp = snapshot.erp_quantity or Decimal("0")
        physical = snapshot.physical_quantity or Decimal("0")
        discrepancy = physical - erp
        discrepancy_pct = (abs(discrepancy) / erp * 100) if erp > Decimal("0") else Decimal("0")

        return {
            "discrepancy": discrepancy,
            "discrepancy_percentage": discrepancy_pct.quantize(Decimal("0.01")),
        }

    async def find_affected_production_orders(
        self, session: AsyncSession, material_id: str
    ) -> list[ProductionOrder]:
        stmt = (
            select(ProductionOrder)
            .join(ProductionConsumption, ProductionConsumption.production_order_id == ProductionOrder.production_order_id)
            .where(
                and_(
                    ProductionConsumption.material_id == material_id,
                    ProductionOrder.status.in_(["PLANNED", "IN_PROGRESS"]),
                )
            )
            .order_by(ProductionOrder.planned_start.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def calculate_hours_to_production_stop(
        self, session: AsyncSession, material_id: str
    ) -> float:
        snapshot = await self.get_current_inventory(session, material_id)
        if not snapshot:
            return 0.0

        usable = snapshot.usable_quantity or Decimal("0")
        avg_7d = await self.calculate_average_consumption_7d(session, material_id)

        if avg_7d <= Decimal("0"):
            return float("inf") if usable > Decimal("0") else 0.0

        consumption_per_hour = avg_7d / Decimal("24")
        if consumption_per_hour <= Decimal("0"):
            return float("inf")

        hours = usable / consumption_per_hour
        return float(hours.quantize(Decimal("0.1")))

    async def evaluate_thresholds(
        self, session: AsyncSession, material_id: str, metrics_dict: dict
    ) -> list[dict]:
        stmt = (
            select(RiskThreshold)
            .where(
                and_(
                    RiskThreshold.material_id == material_id,
                    RiskThreshold.active == True,
                )
            )
        )
        result = await session.execute(stmt)
        thresholds = result.scalars().all()

        violations = []
        for t in thresholds:
            value = metrics_dict.get(t.metric_name)
            if value is None:
                continue

            comparison = t.comparison_operator
            warning = t.warning_threshold
            critical = t.critical_threshold

            if comparison == "gt" or comparison == ">":
                if critical is not None and value > critical:
                    violations.append({
                        "metric": t.metric_name,
                        "value": value,
                        "threshold": critical,
                        "severity": "CRITICAL",
                        "unit": t.unit,
                    })
                elif warning is not None and value > warning:
                    violations.append({
                        "metric": t.metric_name,
                        "value": value,
                        "threshold": warning,
                        "severity": "WARNING",
                        "unit": t.unit,
                    })
            elif comparison == "lt" or comparison == "<":
                if critical is not None and value < critical:
                    violations.append({
                        "metric": t.metric_name,
                        "value": value,
                        "threshold": critical,
                        "severity": "CRITICAL",
                        "unit": t.unit,
                    })
                elif warning is not None and value < warning:
                    violations.append({
                        "metric": t.metric_name,
                        "value": value,
                        "threshold": warning,
                        "severity": "WARNING",
                        "unit": t.unit,
                    })

        return violations

    async def calculate_risk(
        self, session: AsyncSession, material_id: str
    ) -> RiskReport:
        snapshot = await self.get_current_inventory(session, material_id)
        usable = (snapshot.usable_quantity or Decimal("0")) if snapshot else Decimal("0")
        erp_qty = (snapshot.erp_quantity or Decimal("0")) if snapshot else Decimal("0")
        physical_qty = (snapshot.physical_quantity or Decimal("0")) if snapshot else Decimal("0")

        avg_30d = await self.calculate_average_consumption_30d(session, material_id)
        avg_7d = await self.calculate_average_consumption_7d(session, material_id)

        coverage_data = await self.calculate_inventory_coverage(session, material_id)
        coverage_days = coverage_data["coverage_days"]
        trend = coverage_data["trend"]

        disc_data = await self.calculate_inventory_discrepancy(session, material_id)
        discrepancy = disc_data["discrepancy"]
        disc_pct = disc_data["discrepancy_percentage"]

        affected = await self.find_affected_production_orders(session, material_id)
        hours_stop = await self.calculate_hours_to_production_stop(session, material_id)

        metrics_dict = {
            "coverage_days": coverage_days,
            "discrepancy_percentage": disc_pct,
            "usable_quantity": usable,
        }
        violations = await self.evaluate_thresholds(session, material_id, metrics_dict)

        coverage_float = float(coverage_days)
        disc_float = float(disc_pct)

        if coverage_float < 3 or disc_float > 20:
            risk_level = "CRITICAL"
        elif coverage_float < 7:
            risk_level = "HIGH"
        elif coverage_float < 14:
            risk_level = "MEDIUM"
        elif coverage_float < 21:
            risk_level = "LOW"
        else:
            risk_level = "NONE"

        trend_label = "CONSUMPTION INCREASING" if trend == "INCREASING" else (
            "CONSUMPTION DECREASING" if trend == "DECREASING" else "STABLE"
        )

        return RiskReport(
            material_id=material_id,
            risk_level=risk_level,
            usable_stock=usable,
            avg_daily_consumption_30d=avg_30d,
            avg_daily_consumption_7d=avg_7d,
            coverage_days=coverage_days,
            inventory_discrepancy=discrepancy,
            discrepancy_percentage=disc_pct,
            erp_quantity=erp_qty,
            physical_quantity=physical_qty,
            affected_orders=affected,
            hours_to_production_stop=hours_stop,
            threshold_violations=violations,
            trend_7d_vs_30d=trend_label,
        )
