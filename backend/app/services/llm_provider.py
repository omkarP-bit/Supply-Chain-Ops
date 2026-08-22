from __future__ import annotations

import uuid
from decimal import Decimal


async def get_plan_suggestions(
    incident_id: str,
    material_id: str | None,
    risk_report: dict,
    eligible_suppliers: list[dict],
) -> list[dict]:
    suggestions: list[dict] = []

    coverage = float(risk_report.get("coverage_days", 0))
    risk_level = risk_report.get("risk_level", "UNKNOWN")
    hours_to_stop = float(risk_report.get("hours_to_production_stop", 0))

    suppliers_with_stock = [
        s for s in eligible_suppliers
        if s.get("rejection_reason") is None and float(s.get("available_quantity", 0)) > 0
    ]

    if suppliers_with_stock:
        best = suppliers_with_stock[0]
        suggestions.append({
            "plan_id": str(uuid.uuid4().hex[:16]),
            "plan_name": f"Emergency procurement from {best.get('supplier_name', 'supplier')}",
            "plan_type": "EMERGENCY_PROCUREMENT",
            "plan_details": {
                "supplier_id": best.get("supplier_id"),
                "supplier_name": best.get("supplier_name"),
                "quantity": str(best.get("available_quantity", 0)),
                "unit_price": str(best.get("unit_price", 0)),
                "lead_time_days": best.get("lead_time_days", 0),
                "rationale": f"Fastest qualified supplier with {best.get('lead_time_days', '?')}d lead time",
            },
            "estimated_cost": float(best.get("unit_price", 0)) * 100,
            "estimated_delivery_days": float(best.get("lead_time_days", 30)),
            "production_impact_hours": hours_to_stop,
            "supplier_risk_score": float(100 - float(best.get("reliability_score", 50))),
            "quality_score": float(best.get("quality_score", 50)),
            "robustness_score": 70.0,
        })

    if coverage < 3 and risk_level in ("CRITICAL", "HIGH"):
        suggestions.append({
            "plan_id": str(uuid.uuid4().hex[:16]),
            "plan_name": "Production schedule adjustment",
            "plan_type": "PRODUCTION_ADJUSTMENT",
            "plan_details": {
                "action": "Defer non-critical production runs by 5-7 days",
                "estimated_savings_hours": hours_to_stop * 0.3,
                "rationale": f"Only {coverage:.1f} days of coverage; production stop imminent",
            },
            "estimated_cost": 5000.0,
            "estimated_delivery_days": 7.0,
            "production_impact_hours": hours_to_stop * 0.3,
            "supplier_risk_score": 0.0,
            "quality_score": 60.0,
            "robustness_score": 55.0,
        })

    if not suggestions:
        suggestions.append({
            "plan_id": str(uuid.uuid4().hex[:16]),
            "plan_name": "Monitor and reassess",
            "plan_type": "MONITORING",
            "plan_details": {
                "action": "Continue monitoring inventory levels",
                "rationale": f"Current risk level: {risk_level}; no immediate action required",
            },
            "estimated_cost": 0.0,
            "estimated_delivery_days": 0.0,
            "production_impact_hours": 0.0,
            "supplier_risk_score": 0.0,
            "quality_score": 80.0,
            "robustness_score": 90.0,
        })

    for s in suggestions:
        s["overall_score"] = round(
            (s.get("quality_score", 0) * 0.4
             + (100 - s.get("supplier_risk_score", 0)) * 0.3
             + s.get("robustness_score", 0) * 0.3),
            2,
        )

    return suggestions
