from __future__ import annotations

import json
import uuid
from decimal import Decimal

import httpx

from app.config import settings


async def get_plan_suggestions(
    incident_id: str,
    material_id: str | None,
    risk_report: dict,
    eligible_suppliers: list[dict],
) -> list[dict]:
    if settings.llm_provider.lower() == "groq" and settings.llm_api_key:
        try:
            return await _get_groq_suggestions(
                incident_id, material_id, risk_report, eligible_suppliers
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            pass

    return _get_deterministic_suggestions(risk_report, eligible_suppliers)


async def _get_groq_suggestions(
    incident_id: str,
    material_id: str | None,
    risk_report: dict,
    eligible_suppliers: list[dict],
) -> list[dict]:
    prompt = {
        "incident_id": incident_id,
        "material_id": material_id,
        "risk_report": risk_report,
        "eligible_suppliers": eligible_suppliers,
    }
    response_schema = (
        "Return a JSON object with a 'suggestions' array. Each suggestion must contain "
        "plan_name, plan_type, plan_details, estimated_cost, estimated_delivery_days, "
        "production_impact_hours, supplier_risk_score, quality_score, and robustness_score. "
        "Use only the supplied risk report and eligible suppliers. Do not invent supplier IDs, "
        "quantities, prices, or lead times."
    )

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a supply-chain recovery recommendation assistant. "
                            "Deterministic services have established operational truth. "
                            + response_schema
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)

    suggestions = payload["suggestions"]
    if not isinstance(suggestions, list) or not suggestions:
        raise ValueError("Groq returned no recovery suggestions")

    normalized = []
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            raise ValueError("Groq returned an invalid suggestion")
        suggestion["plan_id"] = str(uuid.uuid4().hex[:16])
        suggestion["plan_details"] = suggestion.get("plan_details", {})
        suggestion["overall_score"] = round(
            float(suggestion.get("quality_score", 0)) * 0.4
            + (100 - float(suggestion.get("supplier_risk_score", 0))) * 0.3
            + float(suggestion.get("robustness_score", 0)) * 0.3,
            2,
        )
        normalized.append(suggestion)
    return normalized


def _get_deterministic_suggestions(
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
                "quantity": str(min(float(best.get("available_quantity", 0)), 100.0)),
                "unit_price": str(best.get("unit_price", 0)),
                "lead_time_days": best.get("lead_time_days", 0),
                "rationale": f"Fastest qualified supplier with {best.get('lead_time_days', '?')}d lead time",
            },
            "estimated_cost": float(best.get("unit_price", 0))
            * min(float(best.get("available_quantity", 0)), 100.0),
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
